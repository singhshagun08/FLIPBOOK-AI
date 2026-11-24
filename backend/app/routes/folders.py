
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.folder_service import (
    create_folder,
    list_folders,
    get_folder_details,
    update_folder,
    delete_folder,
    FolderServiceError,
)
from app.utils.responses import success_response, error_response


folders_bp = Blueprint("folders", __name__)


def get_current_user_id():
    """Get the authenticated user's database ID."""

    identity = get_jwt_identity()

    try:
        return int(identity)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------
# 1. CREATE FOLDER
# POST /api/folders
# ---------------------------------------------------------

@folders_bp.route("", methods=["POST"])
@jwt_required()
def create_folder_route():

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

    try:
        folder = create_folder(
            user_id=user_id,
            name=data.get("name"),
            description=data.get("description"),
            parent_folder_id=data.get("parent_folder_id"),
            color=data.get("color", "#64748b")
        )

        return success_response(
            message="Folder created successfully.",
            data=folder.to_dict(),
            status_code=201
        )

    except FolderServiceError as exc:
        return error_response(str(exc), status_code=400)

    except Exception:
        current_app.logger.exception("Folder creation failed.")

        return error_response(
            "Unable to create folder.",
            status_code=500
        )


# ---------------------------------------------------------
# 2. LIST FOLDERS
# GET /api/folders
# ---------------------------------------------------------

@folders_bp.route("", methods=["GET"])
@jwt_required()
def list_folders_route():

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    parent_folder_value = request.args.get("parent_folder_id")

    parent_folder_id = None

    if parent_folder_value is not None:
        try:
            parent_folder_id = int(parent_folder_value)
        except ValueError:
            return error_response(
                "Invalid parent folder ID.",
                status_code=400
            )

    try:
        folders = list_folders(
            user_id=user_id,
            parent_folder_id=parent_folder_id
        )

        return success_response(
            message="Folders retrieved successfully.",
            data={
                "folders": [
                    folder.to_dict()
                    for folder in folders
                ],
                "total": len(folders)
            }
        )

    except FolderServiceError as exc:
        return error_response(str(exc), status_code=404)

    except Exception:
        current_app.logger.exception("Folder listing failed.")

        return error_response(
            "Unable to retrieve folders.",
            status_code=500
        )


# ---------------------------------------------------------
# 3. GET FOLDER DETAILS
# GET /api/folders/<folder_id>
# ---------------------------------------------------------

@folders_bp.route("/<int:folder_id>", methods=["GET"])
@jwt_required()
def get_folder_route(folder_id):

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    try:
        folder = get_folder_details(
            folder_id=folder_id,
            user_id=user_id
        )

        return success_response(
            message="Folder retrieved successfully.",
            data=folder.to_dict(include_children=True)
        )

    except FolderServiceError as exc:
        return error_response(str(exc), status_code=404)

    except Exception:
        current_app.logger.exception("Folder retrieval failed.")

        return error_response(
            "Unable to retrieve folder.",
            status_code=500
        )


# ---------------------------------------------------------
# 4. UPDATE FOLDER
# PUT /api/folders/<folder_id>
# ---------------------------------------------------------

@folders_bp.route("/<int:folder_id>", methods=["PUT"])
@jwt_required()
def update_folder_route(folder_id):

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
        "name",
        "description",
        "parent_folder_id",
        "color"
    }

    if not data or not set(data).issubset(allowed_fields):
        return error_response(
            "Provide valid folder fields to update.",
            status_code=400
        )

    try:
        update_arguments = {
            "folder_id": folder_id,
            "user_id": user_id
        }

        if "name" in data:
            update_arguments["name"] = data["name"]

        if "description" in data:
            update_arguments["description"] = data["description"]

        if "parent_folder_id" in data:
            parent_id = data["parent_folder_id"]

            if parent_id is not None:
                if isinstance(parent_id, bool) or not isinstance(parent_id, int):
                    return error_response(
                        "Parent folder ID must be an integer or null.",
                        status_code=400
                    )

            update_arguments["parent_folder_id"] = parent_id

        if "color" in data:
            update_arguments["color"] = data["color"]

        folder = update_folder(**update_arguments)

        return success_response(
            message="Folder updated successfully.",
            data=folder.to_dict()
        )

    except FolderServiceError as exc:
        return error_response(str(exc), status_code=400)

    except Exception:
        current_app.logger.exception("Folder update failed.")

        return error_response(
            "Unable to update folder.",
            status_code=500
        )


# ---------------------------------------------------------
# 5. DELETE FOLDER
# DELETE /api/folders/<folder_id>
# ---------------------------------------------------------

@folders_bp.route("/<int:folder_id>", methods=["DELETE"])
@jwt_required()
def delete_folder_route(folder_id):

    user_id = get_current_user_id()

    if user_id is None:
        return error_response(
            "Invalid authenticated user.",
            status_code=401
        )

    try:
        delete_folder(
            folder_id=folder_id,
            user_id=user_id
        )

        return success_response(
            message="Folder and its nested folders deleted successfully. Documents have been preserved."
        )

    except FolderServiceError as exc:
        return error_response(str(exc), status_code=404)

    except Exception:
        current_app.logger.exception("Folder deletion failed.")

        return error_response(
            "Unable to delete folder.",
            status_code=500
        )
