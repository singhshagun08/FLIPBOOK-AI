
from pathlib import Path

from flask import Blueprint, current_app, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Document, Folder, DocumentChunk

from app.services.document_service import (
    upload_document,
    DocumentServiceError,
)

from app.services.pdf_processing_service import (
    process_document,
    PDFProcessingError,
)

from app.services.vector_store_service import (
    get_vector_store_service,
    VectorStoreError,
)

from app.utils.responses import success_response, error_response


documents_bp = Blueprint("documents", __name__)


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


def get_owned_document(document_id, user_id):
    """Fetch a document only if it belongs to the current user."""

    return Document.query.filter_by(
        id=document_id,
        user_id=user_id
    ).first()


def get_safe_document_path(document):
    """Resolve a stored PDF path and verify its storage location."""

    upload_root = Path(
        current_app.config["UPLOAD_FOLDER"]
    ).resolve()

    user_directory = (
        upload_root / f"user_{document.user_id}"
    ).resolve()

    document_path = Path(document.file_path).resolve()

    if not document_path.is_relative_to(user_directory):
        raise ValueError("Invalid document storage path.")

    return document_path


# ============================================================
# 1. UPLOAD DOCUMENT
# POST /api/documents/upload
# ============================================================

@documents_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_pdf():

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    uploaded_file = request.files.get("file")

    if uploaded_file is None:
        return error_response(
            "Please provide a PDF file using the 'file' field.",
            status_code=400
        )

    title = request.form.get("title")
    description = request.form.get("description")
    folder_id_value = request.form.get("folder_id")

    folder_id = None

    if folder_id_value:
        try:
            folder_id = int(folder_id_value)
        except (TypeError, ValueError):
            return error_response(
                "Invalid folder ID.",
                status_code=400
            )

    try:
        document = upload_document(
            file=uploaded_file,
            user_id=user_id,
            title=title,
            description=description,
            folder_id=folder_id
        )

        return success_response(
            message="Document uploaded successfully.",
            data=document.to_dict(),
            status_code=201
        )

    except DocumentServiceError as exc:
        return error_response(
            str(exc),
            status_code=400
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Document upload failed.")

        return error_response(
            "Unable to upload document.",
            status_code=500
        )


# ============================================================
# 2. LIST DOCUMENTS
# GET /api/documents
# ============================================================

@documents_bp.route("", methods=["GET"])
@jwt_required()
def list_documents():

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        if page is None or per_page is None or page < 1:
            return error_response(
                "Page must be a positive integer.",
                status_code=400
            )

        if per_page < 1 or per_page > 100:
            return error_response(
                "per_page must be between 1 and 100.",
                status_code=400
            )

        query = Document.query.filter_by(user_id=user_id)

        folder_id = request.args.get("folder_id")

        if folder_id is not None:
            try:
                folder_id = int(folder_id)
            except ValueError:
                return error_response(
                    "Invalid folder ID.",
                    status_code=400
                )

            query = query.filter_by(folder_id=folder_id)

        favorite = request.args.get("favorite")

        if favorite is not None:
            if favorite.lower() not in ("true", "false"):
                return error_response(
                    "favorite must be true or false.",
                    status_code=400
                )

            query = query.filter_by(
                is_favorite=(favorite.lower() == "true")
            )

        pagination = query.order_by(
            Document.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return success_response(
            message="Documents retrieved successfully.",
            data={
                "documents": [
                    document.to_dict()
                    for document in pagination.items
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
        current_app.logger.exception("Document listing failed.")

        return error_response(
            "Unable to retrieve documents.",
            status_code=500
        )


# ============================================================
# 3. GET DOCUMENT DETAILS
# GET /api/documents/<document_id>
# ============================================================

@documents_bp.route("/<int:document_id>", methods=["GET"])
@jwt_required()
def get_document(document_id):

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    document = get_owned_document(document_id, user_id)

    if document is None:
        return error_response(
            "Document not found.",
            status_code=404
        )

    return success_response(
        message="Document retrieved successfully.",
        data=document.to_dict()
    )


# ============================================================
# 4. UPDATE DOCUMENT
# PUT /api/documents/<document_id>
# ============================================================

@documents_bp.route("/<int:document_id>", methods=["PUT"])
@jwt_required()
def update_document(document_id):

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    document = get_owned_document(document_id, user_id)

    if document is None:
        return error_response(
            "Document not found.",
            status_code=404
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
        "folder_id",
        "is_favorite"
    }

    if not data or not set(data).issubset(allowed_fields):
        return error_response(
            "Provide valid document fields to update.",
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

        document.title = title.strip()

    if "description" in data:
        description = data["description"]

        if description is not None and not isinstance(description, str):
            return error_response(
                "Description must be text.",
                status_code=400
            )

        document.description = description

    if "folder_id" in data:
        folder_id = data["folder_id"]

        if folder_id is not None:
            if isinstance(folder_id, bool) or not isinstance(folder_id, int):
                return error_response(
                    "Folder ID must be an integer or null.",
                    status_code=400
                )

            folder = db.session.get(Folder, folder_id)

            if folder is None or folder.user_id != user_id:
                return error_response(
                    "Folder not found or access denied.",
                    status_code=404
                )

        document.folder_id = folder_id

    if "is_favorite" in data:
        if not isinstance(data["is_favorite"], bool):
            return error_response(
                "is_favorite must be true or false.",
                status_code=400
            )

        document.is_favorite = data["is_favorite"]

    try:
        db.session.commit()

        return success_response(
            message="Document updated successfully.",
            data=document.to_dict()
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Document update failed.")

        return error_response(
            "Unable to update document.",
            status_code=500
        )


# ============================================================
# 5. DELETE DOCUMENT
# DELETE /api/documents/<document_id>
# ============================================================

@documents_bp.route("/<int:document_id>", methods=["DELETE"])
@jwt_required()
def delete_document(document_id):

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    document = get_owned_document(document_id, user_id)

    if document is None:
        return error_response(
            "Document not found.",
            status_code=404
        )

    try:
        document_path = get_safe_document_path(document)

        db.session.delete(document)
        db.session.commit()

        # Delete the physical file after the database commit.
        if document_path.is_file():
            document_path.unlink()

        return success_response(
            message="Document deleted successfully."
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Document deletion failed.")

        return error_response(
            "Unable to delete document.",
            status_code=500
        )


# ============================================================
# 6. DOWNLOAD DOCUMENT
# GET /api/documents/<document_id>/download
# ============================================================

@documents_bp.route(
    "/<int:document_id>/download",
    methods=["GET"]
)
@jwt_required()
def download_document(document_id):

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    document = get_owned_document(document_id, user_id)

    if document is None:
        return error_response(
            "Document not found.",
            status_code=404
        )

    try:
        document_path = get_safe_document_path(document)

        if not document_path.is_file():
            return error_response(
                "Document file is missing from storage.",
                status_code=404
            )

        return send_file(
            document_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=document.original_filename
        )

    except Exception:
        current_app.logger.exception("Document download failed.")

        return error_response(
            "Unable to download document.",
            status_code=500
        )


# ============================================================
# 7. PROCESS PDF DOCUMENT
# POST /api/documents/<document_id>/process
# ============================================================

@documents_bp.route(
    "/<int:document_id>/process",
    methods=["POST"]
)
@jwt_required()
def process_document_api(document_id):
    """
    Extract PDF text, generate chunks, create embeddings,
    and index the document in ChromaDB.
    """

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid user identity.",
            status_code=401
        )

    document = get_owned_document(document_id, user_id)

    if document is None:
        return error_response(
            "Document not found.",
            status_code=404
        )

    try:
        # Step 1: Extract PDF text and generate document chunks.
        process_document(
            document_id=document_id,
            user_id=user_id
        )

        # Step 2: Generate embeddings and index chunks in ChromaDB.
        vector_store = get_vector_store_service()

        vector_store.index_document(
            document_id=document_id,
            user_id=user_id
        )

        # Step 3: Reload the updated document.
        document = get_owned_document(document_id, user_id)

        if document is None:
            raise RuntimeError(
                "Document could not be retrieved after processing."
            )

        metadata = document.extracted_metadata or {}
        extraction = metadata.get("extraction", {})

        # Step 4: Return processing and indexing results.
        return success_response(
            message="Document processed and indexed successfully.",
            data={
                "document": document.to_dict(),
                "processing_status": document.processing_status,
                "indexing_status": "completed",
                "page_count": document.page_count,
                "chunk_count": extraction.get("chunk_count", 0),
                "extracted_page_count": extraction.get(
                    "extracted_page_count", 0
                ),
                "extracted_metadata": metadata
            },
            status_code=200
        )

    except PDFProcessingError as exc:
        document = get_owned_document(document_id, user_id)

        return error_response(
            message="Document processing failed.",
            errors={
                "details": str(exc),
                "processing_status": (
                    document.processing_status
                    if document else "failed"
                )
            },
            status_code=422
        )

    except VectorStoreError as exc:
        current_app.logger.exception(
            "Document vector indexing failed."
        )

        return error_response(
            message=(
                "PDF processing succeeded, but vector indexing failed."
            ),
            errors={
                "details": str(exc),
                "processing_status": "completed",
                "indexing_status": "failed"
            },
            status_code=502
        )

    except Exception:
        current_app.logger.exception(
            "Unexpected document processing error."
        )

        return error_response(
            "An unexpected error occurred during document processing.",
            status_code=500
        )


# ============================================================
# 8. GET DOCUMENT CHUNKS
# GET /api/documents/<document_id>/chunks
# ============================================================

@documents_bp.route(
    "/<int:document_id>/chunks",
    methods=["GET"]
)
@jwt_required()
def get_document_chunks(document_id):
    """
    Retrieve extracted document chunks with pagination.
    """

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid user identity.",
            status_code=401
        )

    document = get_owned_document(document_id, user_id)

    if document is None:
        return error_response(
            "Document not found.",
            status_code=404
        )

    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        if page < 1:
            return error_response(
                "Page must be greater than zero.",
                status_code=400
            )

        if per_page < 1 or per_page > 100:
            return error_response(
                "per_page must be between 1 and 100.",
                status_code=400
            )

        pagination = (
            DocumentChunk.query
            .filter_by(
                document_id=document_id,
                user_id=user_id
            )
            .order_by(DocumentChunk.chunk_index.asc())
            .paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
        )

        chunks = [
            chunk.to_dict()
            for chunk in pagination.items
        ]

        return success_response(
            message="Document chunks retrieved successfully.",
            data={
                "document_id": document_id,
                "chunks": chunks,
                "pagination": {
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev
                }
            }
        )

    except Exception:
        current_app.logger.exception(
            "Failed to retrieve document chunks."
        )

        return error_response(
            "Unable to retrieve document chunks.",
            status_code=500
        )


# ============================================================
# 9. GET DOCUMENT PROCESSING STATUS
# GET /api/documents/<document_id>/processing-status
# ============================================================

@documents_bp.route(
    "/<int:document_id>/processing-status",
    methods=["GET"]
)
@jwt_required()
def get_document_processing_status(document_id):
    """
    Retrieve the PDF processing status.
    """

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid user identity.",
            status_code=401
        )

    document = get_owned_document(document_id, user_id)

    if document is None:
        return error_response(
            "Document not found.",
            status_code=404
        )

    # Extraction information is stored inside the
    # nested "extraction" dictionary.
    metadata = document.extracted_metadata or {}
    extraction = metadata.get("extraction", {})

    return success_response(
        message="Document processing status retrieved successfully.",
        data={
            "document_id": document.id,
            "processing_status": document.processing_status,
            "processing_error": document.processing_error,
            "page_count": document.page_count,
            "extracted_page_count": extraction.get(
                "extracted_page_count", 0
            ),
            "chunk_count": extraction.get(
                "chunk_count", 0
            ),
            "extraction_engine": extraction.get(
                "extraction_engine"
            ),
            "text_splitter": extraction.get(
                "text_splitter"
            )
        }
    )
