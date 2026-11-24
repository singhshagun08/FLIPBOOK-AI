import hashlib
import os
import uuid

from pathlib import Path

import fitz

from flask import current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Document, Folder, User


class DocumentServiceError(Exception):
    """Raised when a document operation cannot be completed."""


def validate_pdf(file_bytes, original_filename, max_pages):
    """Validate PDF content and extract its metadata."""

    if not original_filename:
        raise DocumentServiceError("A filename is required.")

    safe_original_name = secure_filename(original_filename)

    if not safe_original_name:
        raise DocumentServiceError("Invalid filename.")

    if Path(safe_original_name).suffix.lower() != ".pdf":
        raise DocumentServiceError("Only PDF files are allowed.")

    if not file_bytes:
        raise DocumentServiceError("The uploaded file is empty.")

    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as pdf:

            if pdf.is_encrypted:
                raise DocumentServiceError(
                    "Password-protected PDFs are not supported."
                )

            page_count = pdf.page_count

            if page_count < 1:
                raise DocumentServiceError(
                    "The PDF does not contain any pages."
                )

            if page_count > max_pages:
                raise DocumentServiceError(
                    f"PDF exceeds the maximum of {max_pages} pages."
                )

            metadata = pdf.metadata or {}

            extracted_metadata = {
                "title": metadata.get("title"),
                "author": metadata.get("author"),
                "subject": metadata.get("subject"),
                "keywords": metadata.get("keywords"),
                "creator": metadata.get("creator"),
                "producer": metadata.get("producer"),
                "creation_date": metadata.get("creationDate"),
                "modification_date": metadata.get("modDate"),
            }

        return safe_original_name, page_count, extracted_metadata

    except DocumentServiceError:
        raise

    except Exception as exc:
        raise DocumentServiceError(
            "The uploaded file is not a valid readable PDF."
        ) from exc


def upload_document(
    file,
    user_id,
    title=None,
    description=None,
    folder_id=None
):
    """
    Validate, store and register an uploaded PDF.

    The file is written atomically. The database record is committed
    only after the file has been successfully stored.
    """

    if file is None:
        raise DocumentServiceError("No file was provided.")

    user = db.session.get(User, user_id)

    if user is None or not user.is_active:
        raise DocumentServiceError("User account is unavailable.")

    if folder_id is not None:
        folder = db.session.get(Folder, folder_id)

        if folder is None or folder.user_id != user.id:
            raise DocumentServiceError(
                "Folder not found or access denied."
            )

    original_filename = file.filename

    max_file_size = current_app.config["MAX_CONTENT_LENGTH"]

    file_bytes = file.read(max_file_size + 1)

    if len(file_bytes) > max_file_size:
        max_size_mb = max_file_size / (1024 * 1024)

        raise DocumentServiceError(
            f"File exceeds the maximum allowed size of "
            f"{max_size_mb:g} MB."
        )

    if not file_bytes:
        raise DocumentServiceError("The uploaded file is empty.")

    max_pages = current_app.config["PDF_MAX_PAGES"]

    safe_original_name, page_count, metadata = validate_pdf(
        file_bytes,
        original_filename,
        max_pages
    )

    checksum = hashlib.sha256(file_bytes).hexdigest()

    duplicate = Document.query.filter_by(
        user_id=user.id,
        checksum=checksum
    ).first()

    if duplicate:
        raise DocumentServiceError(
            "This document has already been uploaded."
        )

    if title is not None and not isinstance(title, str):
        raise DocumentServiceError("Title must be text.")

    document_title = (
        title.strip()
        if isinstance(title, str) and title.strip()
        else Path(safe_original_name).stem
    )

    if len(document_title) > 255:
        raise DocumentServiceError(
            "Document title cannot exceed 255 characters."
        )

    if description is not None and not isinstance(description, str):
        raise DocumentServiceError("Description must be text.")

    stored_filename = f"{uuid.uuid4().hex}.pdf"

    upload_root = Path(
        current_app.config["UPLOAD_FOLDER"]
    ).resolve()

    user_directory = (
        upload_root / f"user_{user.id}"
    ).resolve()

    # Prevent storage outside the configured upload directory.
    if not user_directory.is_relative_to(upload_root):
        raise DocumentServiceError("Invalid upload storage location.")

    user_directory.mkdir(parents=True, exist_ok=True)

    destination = user_directory / stored_filename
    temporary_destination = user_directory / (
        f".{stored_filename}.tmp"
    )

    try:
        # Write to a temporary file first.
        temporary_destination.write_bytes(file_bytes)

        # Atomically move the completed file into its final location.
        os.replace(temporary_destination, destination)

        document = Document(
            user_id=user.id,
            folder_id=folder_id,
            title=document_title,
            original_filename=safe_original_name,
            stored_filename=stored_filename,
            file_path=str(destination),
            mime_type="application/pdf",
            file_size=len(file_bytes),
            page_count=page_count,

            # Text extraction and AI processing are not implemented yet.
            processing_status="pending",

            extracted_metadata=metadata,
            checksum=checksum,
            description=description
        )

        db.session.add(document)
        db.session.commit()

        return document

    except Exception:
        db.session.rollback()

        if temporary_destination.exists():
            temporary_destination.unlink()

        if destination.exists():
            destination.unlink()

        raise