
from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.flashcard_service import (
    get_flashcard_service,
    FlashcardServiceError,
)

from app.utils.responses import success_response, error_response


flashcards_bp = Blueprint("flashcards", __name__)


def get_current_user_id():
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


# ============================================================
# 1. GENERATE AI FLASHCARDS
# POST /api/learning/flashcards/generate
# ============================================================

@flashcards_bp.route(
    "/flashcards/generate",
    methods=["POST"]
)
@jwt_required()
def generate_flashcards():

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
        "document_ids",
        "number_of_cards",
        "difficulty"
    }

    if not set(data).issubset(allowed_fields):
        return error_response(
            "Invalid flashcard generation fields.",
            status_code=400
        )

    document_ids = data.get("document_ids")
    number_of_cards = data.get("number_of_cards", 10)
    difficulty = data.get("difficulty", "medium")

    if not isinstance(document_ids, list) or not document_ids:
        return error_response(
            "Select at least one document.",
            status_code=400
        )

    if (
        not isinstance(number_of_cards, int)
        or isinstance(number_of_cards, bool)
        or not 1 <= number_of_cards <= 30
    ):
        return error_response(
            "number_of_cards must be between 1 and 30.",
            status_code=400
        )

    if difficulty not in ("easy", "medium", "hard"):
        return error_response(
            "Difficulty must be easy, medium, or hard.",
            status_code=400
        )

    try:
        result = get_flashcard_service().generate_flashcards(
            user_id=user_id,
            document_ids=document_ids,
            number_of_cards=number_of_cards,
            difficulty=difficulty
        )

        return success_response(
            message="Flashcards generated successfully.",
            data=result,
            status_code=201
        )

    except FlashcardServiceError as exc:
        return error_response(
            message=str(exc),
            status_code=400
        )

    except Exception:
        current_app.logger.exception(
            "Flashcard generation API failed."
        )

        return error_response(
            "Unable to generate flashcards.",
            status_code=500
        )


# ============================================================
# 2. GET SAVED FLASHCARDS
# GET /api/learning/flashcards
# ============================================================

@flashcards_bp.route(
    "/flashcards",
    methods=["GET"]
)
@jwt_required()
def list_flashcards():

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    try:
        document_id = request.args.get(
            "document_id",
            type=int
        )

        difficulty = request.args.get("difficulty")
        mastered_value = request.args.get("mastered")

        mastered = None

        if mastered_value is not None:

            if mastered_value.lower() not in ("true", "false"):
                return error_response(
                    "mastered must be true or false.",
                    status_code=400
                )

            mastered = mastered_value.lower() == "true"

        result = get_flashcard_service().get_flashcards(
            user_id=user_id,
            document_id=document_id,
            difficulty=difficulty,
            mastered=mastered
        )

        return success_response(
            message="Flashcards retrieved successfully.",
            data=result
        )

    except FlashcardServiceError as exc:
        return error_response(
            message=str(exc),
            status_code=400
        )

    except Exception:
        current_app.logger.exception(
            "Flashcard listing failed."
        )

        return error_response(
            "Unable to retrieve flashcards.",
            status_code=500
        )


# ============================================================
# 3. REVIEW FLASHCARD
# PATCH /api/learning/flashcards/<flashcard_id>/review
# ============================================================

@flashcards_bp.route(
    "/flashcards/<int:flashcard_id>/review",
    methods=["PATCH"]
)
@jwt_required()
def review_flashcard(flashcard_id):

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

    if set(data.keys()) != {"mastered"}:
        return error_response(
            "Only the mastered field is allowed.",
            status_code=400
        )

    if not isinstance(data["mastered"], bool):
        return error_response(
            "Mastered must be true or false.",
            status_code=400
        )

    try:
        result = get_flashcard_service().review_flashcard(
            user_id=user_id,
            flashcard_id=flashcard_id,
            mastered=data["mastered"]
        )

        return success_response(
            message="Flashcard review updated successfully.",
            data={"flashcard": result}
        )

    except FlashcardServiceError as exc:
        return error_response(
            message=str(exc),
            status_code=400
        )

    except Exception:
        current_app.logger.exception(
            "Flashcard review failed."
        )

        return error_response(
            "Unable to update flashcard review.",
            status_code=500
        )


# ============================================================
# 4. DELETE FLASHCARD
# DELETE /api/learning/flashcards/<flashcard_id>
# ============================================================

@flashcards_bp.route(
    "/flashcards/<int:flashcard_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_flashcard(flashcard_id):

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    try:
        result = get_flashcard_service().delete_flashcard(
            user_id=user_id,
            flashcard_id=flashcard_id
        )

        return success_response(
            message="Flashcard deleted successfully.",
            data=result
        )

    except FlashcardServiceError as exc:
        message = str(exc)

        status_code = (
            404
            if message == "Flashcard not found or access denied."
            else 500
        )

        return error_response(
            message=message,
            status_code=status_code
        )

    except Exception:
        current_app.logger.exception(
            "Flashcard deletion API failed."
        )

        return error_response(
            "Unable to delete flashcard.",
            status_code=500
        )
