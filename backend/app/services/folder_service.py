
from app.extensions import db
from app.models import Folder


class FolderServiceError(Exception):
    """Raised when a folder operation cannot be completed."""


_UNSET = object()


def get_owned_folder(folder_id, user_id):
    """Return a folder only when it belongs to the requested user."""

    return Folder.query.filter_by(
        id=folder_id,
        user_id=user_id
    ).first()


def validate_folder_name(name):
    """Validate a folder name."""

    if not isinstance(name, str):
        raise FolderServiceError("Folder name must be text.")

    name = name.strip()

    if not name:
        raise FolderServiceError("Folder name cannot be empty.")

    if len(name) > 150:
        raise FolderServiceError(
            "Folder name cannot exceed 150 characters."
        )

    return name


def validate_folder_color(color):
    """Validate the folder color value."""

    if not isinstance(color, str) or not color.strip():
        raise FolderServiceError(
            "Folder color must be a non-empty string."
        )

    color = color.strip()

    if len(color) > 20:
        raise FolderServiceError(
            "Folder color cannot exceed 20 characters."
        )

    return color


def validate_parent_folder(
    parent_folder_id,
    user_id,
    current_folder_id=None
):
    """Validate parent ownership and prevent circular hierarchies."""

    if parent_folder_id is None:
        return None

    if isinstance(parent_folder_id, bool) or not isinstance(
        parent_folder_id, int
    ):
        raise FolderServiceError(
            "Parent folder ID must be an integer or null."
        )

    parent = get_owned_folder(parent_folder_id, user_id)

    if parent is None:
        raise FolderServiceError(
            "Parent folder not found or access denied."
        )

    if current_folder_id is not None and parent.id == current_folder_id:
        raise FolderServiceError(
            "A folder cannot be its own parent."
        )

    visited = set()
    ancestor = parent

    while ancestor is not None:
        if ancestor.id in visited:
            raise FolderServiceError(
                "Existing folder hierarchy contains a cycle."
            )

        visited.add(ancestor.id)

        if current_folder_id is not None and ancestor.id == current_folder_id:
            raise FolderServiceError(
                "Cannot move a folder inside its own descendant."
            )

        ancestor = ancestor.parent

    return parent


def create_folder(
    user_id,
    name,
    description=None,
    parent_folder_id=None,
    color="#64748b"
):
    """Create a folder for a user."""

    name = validate_folder_name(name)

    if description is not None and not isinstance(description, str):
        raise FolderServiceError("Description must be text.")

    color = validate_folder_color(color)

    validate_parent_folder(
        parent_folder_id,
        user_id
    )

    folder = Folder(
        user_id=user_id,
        name=name,
        description=description,
        parent_folder_id=parent_folder_id,
        color=color
    )

    try:
        db.session.add(folder)
        db.session.commit()
        return folder

    except Exception:
        db.session.rollback()
        raise


def list_folders(user_id, parent_folder_id=None):
    """List root folders or children of a specified folder."""

    if parent_folder_id is not None:
        validate_parent_folder(
            parent_folder_id,
            user_id
        )

    return Folder.query.filter_by(
        user_id=user_id,
        parent_folder_id=parent_folder_id
    ).order_by(
        Folder.name.asc()
    ).all()


def get_folder_details(folder_id, user_id):
    """Retrieve a folder and its nested children."""

    folder = get_owned_folder(folder_id, user_id)

    if folder is None:
        raise FolderServiceError("Folder not found.")

    return folder


def update_folder(
    folder_id,
    user_id,
    name=None,
    description=None,
    parent_folder_id=_UNSET,
    color=None
):
    """Update folder details and optionally move it."""

    folder = get_owned_folder(folder_id, user_id)

    if folder is None:
        raise FolderServiceError("Folder not found.")

    if name is not None:
        folder.name = validate_folder_name(name)

    if description is not None:
        if not isinstance(description, str):
            raise FolderServiceError("Description must be text.")

        folder.description = description

    if parent_folder_id is not _UNSET:
        validate_parent_folder(
            parent_folder_id,
            user_id,
            current_folder_id=folder.id
        )

        folder.parent_folder_id = parent_folder_id

    if color is not None:
        folder.color = validate_folder_color(color)

    try:
        db.session.commit()
        return folder

    except Exception:
        db.session.rollback()
        raise


def delete_folder(folder_id, user_id):
    """
    Delete a folder and its nested folders.

    Documents should be preserved and detached from deleted folders.
    """

    folder = get_owned_folder(folder_id, user_id)

    if folder is None:
        raise FolderServiceError("Folder not found.")

    try:
        # Explicitly detach documents before deleting the folder tree.
        # This avoids relying solely on database cascade behavior.
        folder_ids = []

        def collect_folder_ids(current_folder):
            folder_ids.append(current_folder.id)

            for child in current_folder.children:
                collect_folder_ids(child)

        collect_folder_ids(folder)

        Document = db.Model.registry._class_registry.get("Document")

        if Document is None:
            raise FolderServiceError(
                "Document model is not registered."
            )

        Document.query.filter(
            Document.folder_id.in_(folder_ids)
        ).update(
            {Document.folder_id: None},
            synchronize_session="fetch"
        )

        db.session.delete(folder)
        db.session.commit()

        return True

    except Exception:
        db.session.rollback()
        raise
