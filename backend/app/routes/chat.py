
import time
from datetime import datetime, timezone

from sqlalchemy import or_

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.rag_service import (
    get_rag_service,
    RAGServiceError,
)

from app.extensions import db
from app.models import Document
from app.models.chat import ChatSession, ChatMessage
from app.utils.responses import success_response, error_response


chat_bp = Blueprint("chat", __name__)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_current_user_id():
    """Return the authenticated user's database ID."""
    identity = get_jwt_identity()

    try:
        return int(identity)
    except (TypeError, ValueError):
        return None


def get_owned_session(session_id, user_id):
    """Fetch a chat session belonging to the current user."""
    return ChatSession.query.filter_by(
        id=session_id,
        user_id=user_id
    ).first()


def validate_document_ids(document_ids, user_id):
    """
    Validate that document IDs are a list of unique integers
    and that every document belongs to the authenticated user.
    """
    if not isinstance(document_ids, list):
        raise ValueError("document_ids must be a list.")

    if any(
        isinstance(document_id, bool)
        or not isinstance(document_id, int)
        or document_id <= 0
        for document_id in document_ids
    ):
        raise ValueError(
            "Every document ID must be a positive integer."
        )

    unique_ids = list(dict.fromkeys(document_ids))

    if not unique_ids:
        return []

    documents = Document.query.filter(
        Document.id.in_(unique_ids),
        Document.user_id == user_id
    ).all()

    if len(documents) != len(unique_ids):
        raise LookupError(
            "One or more documents were not found or access was denied."
        )

    return documents


# ============================================================
# 1. CREATE CHAT SESSION
# POST /api/chat/sessions
# ============================================================

@chat_bp.route("/sessions", methods=["POST"])
@jwt_required()
def create_chat_session():

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response(
            "A valid JSON object is required.",
            status_code=400
        )

    allowed_fields = {
        "title",
        "description",
        "document_ids"
    }

    if not set(data).issubset(allowed_fields):
        return error_response(
            "Only title, description, and document_ids are allowed.",
            status_code=400
        )

    title = data.get("title", "New conversation")

    if not isinstance(title, str) or not title.strip():
        return error_response(
            "Title must be a non-empty string.",
            status_code=400
        )

    if len(title.strip()) > 255:
        return error_response(
            "Title cannot exceed 255 characters.",
            status_code=400
        )

    description = data.get("description")

    if (
        description is not None
        and not isinstance(description, str)
    ):
        return error_response(
            "Description must be text or null.",
            status_code=400
        )

    if (
        description is not None
        and len(description) > 5000
    ):
        return error_response(
            "Description cannot exceed 5000 characters.",
            status_code=400
        )

    document_ids = data.get("document_ids", [])

    try:
        documents = validate_document_ids(
            document_ids,
            user_id
        )

        session = ChatSession(
            user_id=user_id,
            title=title.strip(),
            description=description
        )

        session.documents = documents

        db.session.add(session)
        db.session.commit()

        return success_response(
            message="Chat session created successfully.",
            data=session.to_dict(),
            status_code=201
        )

    except ValueError as exc:
        return error_response(
            str(exc),
            status_code=400
        )

    except LookupError as exc:
        return error_response(
            str(exc),
            status_code=404
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Chat session creation failed."
        )

        return error_response(
            "Unable to create chat session.",
            status_code=500
        )


# ============================================================
# 2. LIST, SEARCH AND PAGINATE CHAT SESSIONS
# GET /api/chat/sessions
# ============================================================

@chat_bp.route("/sessions", methods=["GET"])
@jwt_required()
def list_chat_sessions():

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        archived = request.args.get("archived")
        search = request.args.get("search", "").strip()

        if page is None or page < 1:
            return error_response(
                "Page must be a positive integer.",
                status_code=400
            )

        if per_page is None or per_page < 1 or per_page > 100:
            return error_response(
                "per_page must be between 1 and 100.",
                status_code=400
            )

        if len(search) > 100:
            return error_response(
                "Search cannot exceed 100 characters.",
                status_code=400
            )

        # Only retrieve the current user's conversations.
        query = ChatSession.query.filter_by(
            user_id=user_id
        )

        # Archived conversation filter.
        if archived is not None:

            if archived.lower() not in ("true", "false"):
                return error_response(
                    "archived must be true or false.",
                    status_code=400
                )

            query = query.filter_by(
                is_archived=(archived.lower() == "true")
            )

        # Search conversation titles and descriptions.
        if search:
            search_term = f"%{search}%"

            query = query.filter(
                or_(
                    ChatSession.title.ilike(search_term),
                    ChatSession.description.ilike(search_term)
                )
            )

        # Order and paginate conversations.
        pagination = query.order_by(
            ChatSession.updated_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return success_response(
            message="Chat sessions retrieved successfully.",
            data={
                "sessions": [
                    session.to_dict()
                    for session in pagination.items
                ],
                "pagination": {
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_previous": pagination.has_prev
                }
            }
        )

    except Exception:
        current_app.logger.exception(
            "Chat session listing failed."
        )

        return error_response(
            "Unable to retrieve chat sessions.",
            status_code=500
        )


# ============================================================
# 3. GET CHAT SESSION AND MESSAGE HISTORY
# GET /api/chat/sessions/<session_id>
# ============================================================

@chat_bp.route(
    "/sessions/<int:session_id>",
    methods=["GET"]
)
@jwt_required()
def get_chat_session(session_id):

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    session = get_owned_session(
        session_id,
        user_id
    )

    if session is None:
        return error_response(
            "Chat session not found.",
            status_code=404
        )

    try:
        messages = [
            message.to_dict()
            for message in session.messages
        ]

        data = session.to_dict()
        data["messages"] = messages

        return success_response(
            message="Chat session retrieved successfully.",
            data=data
        )

    except Exception:
        current_app.logger.exception(
            "Chat history retrieval failed."
        )

        return error_response(
            "Unable to retrieve chat history.",
            status_code=500
        )


# ============================================================
# 4. UPDATE CHAT SESSION
# PUT /api/chat/sessions/<session_id>
# ============================================================

@chat_bp.route(
    "/sessions/<int:session_id>",
    methods=["PUT"]
)
@jwt_required()
def update_chat_session(session_id):

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    session = get_owned_session(
        session_id,
        user_id
    )

    if session is None:
        return error_response(
            "Chat session not found.",
            status_code=404
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return error_response(
            "A non-empty JSON object is required.",
            status_code=400
        )

    allowed_fields = {
        "title",
        "description",
        "is_archived",
        "document_ids"
    }

    if not set(data).issubset(allowed_fields):
        return error_response(
            "Provide valid chat session fields.",
            status_code=400
        )

    if "title" in data:
        title = data["title"]

        if not isinstance(title, str) or not title.strip():
            return error_response(
                "Title must be a non-empty string.",
                status_code=400
            )

        if len(title.strip()) > 255:
            return error_response(
                "Title cannot exceed 255 characters.",
                status_code=400
            )

        session.title = title.strip()

    if "description" in data:
        description = data["description"]

        if (
            description is not None
            and not isinstance(description, str)
        ):
            return error_response(
                "Description must be text or null.",
                status_code=400
            )

        if (
            description is not None
            and len(description) > 5000
        ):
            return error_response(
                "Description cannot exceed 5000 characters.",
                status_code=400
            )

        session.description = description

    if "is_archived" in data:

        if not isinstance(data["is_archived"], bool):
            return error_response(
                "is_archived must be true or false.",
                status_code=400
            )

        session.is_archived = data["is_archived"]

    if "document_ids" in data:
        try:
            documents = validate_document_ids(
                data["document_ids"],
                user_id
            )

            session.documents = documents

        except ValueError as exc:
            return error_response(
                str(exc),
                status_code=400
            )

        except LookupError as exc:
            return error_response(
                str(exc),
                status_code=404
            )

    try:
        db.session.commit()

        return success_response(
            message="Chat session updated successfully.",
            data=session.to_dict()
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Chat session update failed."
        )

        return error_response(
            "Unable to update chat session.",
            status_code=500
        )


# ============================================================
# 5. DELETE CHAT SESSION
# DELETE /api/chat/sessions/<session_id>
# ============================================================

@chat_bp.route(
    "/sessions/<int:session_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_chat_session(session_id):

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    session = get_owned_session(
        session_id,
        user_id
    )

    if session is None:
        return error_response(
            "Chat session not found.",
            status_code=404
        )

    try:
        db.session.delete(session)
        db.session.commit()

        return success_response(
            message="Chat session deleted successfully."
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Chat session deletion failed."
        )

        return error_response(
            "Unable to delete chat session.",
            status_code=500
        )


# ============================================================
# 6. SEND MESSAGE TO AI RESEARCH ASSISTANT
# POST /api/chat/sessions/<session_id>/messages
# ============================================================

@chat_bp.route(
    "/sessions/<int:session_id>/messages",
    methods=["POST"]
)
@jwt_required()
def send_chat_message(session_id):
    """
    Generate a document-grounded AI response and save
    both the user question and assistant response.
    """

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    session = get_owned_session(
        session_id,
        user_id
    )

    if session is None:
        return error_response(
            "Chat session not found.",
            status_code=404
        )

    if session.is_archived:
        return error_response(
            "Cannot send messages to an archived chat session.",
            status_code=409
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response(
            "A valid JSON object is required.",
            status_code=400
        )

    if not set(data).issubset({"question", "top_k"}):
        return error_response(
            "Only question and top_k are allowed.",
            status_code=400
        )

    question = data.get("question")

    if not isinstance(question, str) or not question.strip():
        return error_response(
            "Question must be a non-empty string.",
            status_code=400
        )

    question = question.strip()

    if len(question) > 10000:
        return error_response(
            "Question cannot exceed 10000 characters.",
            status_code=400
        )

    top_k = data.get("top_k", 5)

    if (
        not isinstance(top_k, int)
        or isinstance(top_k, bool)
        or top_k < 1
        or top_k > 20
    ):
        return error_response(
            "top_k must be an integer between 1 and 20.",
            status_code=400
        )

    # Use only documents explicitly selected for this session.
    document_ids = [
        document.id
        for document in session.documents
    ]

    if not document_ids:
        return error_response(
            "Select at least one document before asking a question.",
            status_code=400
        )

    try:
        rag_service = get_rag_service()

        start_time = time.perf_counter()

        result = rag_service.generate_answer(
            question=question,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k
        )

        response_time_ms = round(
            (time.perf_counter() - start_time) * 1000
        )

        # Save the user's question.
        user_message = ChatMessage(
            chat_session_id=session.id,
            role="user",
            content=question,
            extra_data={
                "document_ids": document_ids
            }
        )

        # Save the AI-generated response.
        assistant_message = ChatMessage(
            chat_session_id=session.id,
            role="assistant",
            content=result["answer"],
            model_name=result["model"],
            response_time_ms=response_time_ms,
            sources=result["sources"],
            extra_data={
                "grounded": result["grounded"],
                "retrieved_count": result["retrieved_count"],
                "top_k": top_k
            }
        )

        db.session.add(user_message)
        db.session.add(assistant_message)

        # Explicitly update the session timestamp.
        session.updated_at = datetime.now(timezone.utc)

        # Save both messages together.
        db.session.commit()

        return success_response(
            message="AI response generated successfully.",
            data={
                "session_id": session.id,
                "user_message": user_message.to_dict(),
                "assistant_message": assistant_message.to_dict(),
                "grounded": result["grounded"],
                "retrieved_count": result["retrieved_count"],
                "sources": result["sources"]
            },
            status_code=201
        )

    except RAGServiceError as exc:
        db.session.rollback()

        current_app.logger.exception(
            "RAG message generation failed."
        )

        return error_response(
            message="Unable to generate an AI response.",
            errors={
                "details": str(exc)
            },
            status_code=502
        )

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Unexpected chat message error."
        )

        return error_response(
            "An unexpected error occurred while processing your message.",
            status_code=500
        )
