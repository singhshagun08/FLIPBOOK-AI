
import re
from pathlib import Path

import fitz

from flask import current_app
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.extensions import db
from app.models import Document, DocumentChunk


class PDFProcessingError(Exception):
    """Raised when PDF processing fails."""


def clean_extracted_text(text):
    """
    Normalize extracted PDF text while preserving paragraph boundaries.
    """

    if not isinstance(text, str):
        return ""

    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize spaces and tabs.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def get_secure_document_path(document):
    """
    Resolve the PDF path and ensure it remains inside the owner's
    configured upload directory.
    """

    upload_root = Path(
        current_app.config["UPLOAD_FOLDER"]
    ).resolve()

    user_directory = (
        upload_root / f"user_{document.user_id}"
    ).resolve()

    file_path = Path(document.file_path).resolve()

    if not user_directory.is_relative_to(upload_root):
        raise PDFProcessingError(
            "Invalid document storage directory."
        )

    if not file_path.is_relative_to(user_directory):
        raise PDFProcessingError(
            "Document file is outside its permitted storage directory."
        )

    if not file_path.is_file():
        raise PDFProcessingError(
            "The stored PDF file could not be found."
        )

    return file_path


def extract_pdf_pages(file_path):
    """
    Extract text page by page using PyMuPDF.

    Returns:
        list[dict]: Each item contains page_number and text.
    """

    pages = []

    try:
        with fitz.open(file_path) as pdf:

            if pdf.is_encrypted:
                raise PDFProcessingError(
                    "Password-protected PDFs are not supported."
                )

            if pdf.page_count == 0:
                raise PDFProcessingError(
                    "The PDF does not contain any pages."
                )

            for page_index, page in enumerate(pdf):

                extracted_text = page.get_text("text")
                cleaned_text = clean_extracted_text(
                    extracted_text
                )

                if cleaned_text:
                    pages.append({
                        "page_number": page_index + 1,
                        "text": cleaned_text
                    })

    except PDFProcessingError:
        raise

    except Exception as exc:
        raise PDFProcessingError(
            "Unable to extract text from the PDF."
        ) from exc

    if not pages:
        raise PDFProcessingError(
            "No extractable text was found. "
            "This PDF may contain scanned images and require OCR."
        )

    return pages


def split_pages_into_chunks(
    pages,
    chunk_size=1000,
    chunk_overlap=200
):
    """
    Split each page independently using LangChain.

    Keeping pages separate ensures every chunk has an accurate
    source page number.
    """

    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise PDFProcessingError(
            "Chunk size must be a positive integer."
        )

    if not isinstance(chunk_overlap, int):
        raise PDFProcessingError(
            "Chunk overlap must be an integer."
        )

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise PDFProcessingError(
            "Chunk overlap must be non-negative and smaller "
            "than chunk size."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ],
        add_start_index=True
    )

    chunks = []

    for page in pages:

        page_number = page["page_number"]
        page_text = page["text"]

        split_documents = splitter.create_documents(
            [page_text],
            metadatas=[{
                "page_number": page_number
            }]
        )

        for split_document in split_documents:

            content = split_document.page_content.strip()

            if not content:
                continue

            chunks.append({
                "page_number": page_number,
                "content": content,
                "start_index": split_document.metadata.get(
                    "start_index"
                ),
                "character_count": len(content),
                # Approximate token count, not an exact tokenizer count.
                "token_count": max(1, round(len(content) / 4))
            })

    if not chunks:
        raise PDFProcessingError(
            "Text extraction completed, but no usable chunks were generated."
        )

    return chunks


def process_document(
    document_id,
    user_id,
    chunk_size=1000,
    chunk_overlap=200
):


    document = Document.query.filter_by(
        id=document_id,
        user_id=user_id
    ).first()

    if document is None:
        raise PDFProcessingError(
            "Document not found or access denied."
        )

    # Record processing status before starting expensive operations.
    document.processing_status = "processing"
    document.processing_error = None
    db.session.commit()

    try:
        file_path = get_secure_document_path(document)

        pages = extract_pdf_pages(file_path)

        chunks = split_pages_into_chunks(
            pages,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Prepare database records.
        chunk_records = []

        for index, chunk in enumerate(chunks):

            chunk_records.append(
                DocumentChunk(
                    user_id=document.user_id,
                    document_id=document.id,
                    chunk_index=index,
                    page_number=chunk["page_number"],
                    content=chunk["content"],
                    token_count=chunk["token_count"],
                    chunk_metadata={
                        "start_index": chunk["start_index"],
                        "character_count": chunk["character_count"],
                        "page_number": chunk["page_number"]
                    }
                )
            )

        # Replace previous chunks only after successful extraction.
        DocumentChunk.query.filter_by(
            document_id=document.id,
            user_id=document.user_id
        ).delete(synchronize_session="fetch")

        db.session.add_all(chunk_records)

        document.processing_status = "completed"
        document.processing_error = None

        document.extracted_metadata = {
            **(document.extracted_metadata or {}),
            "extraction": {
                "page_count": len(pages),
                "extracted_page_count": len(pages),
                "chunk_count": len(chunk_records),
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "extraction_engine": "PyMuPDF",
                "text_splitter": "LangChain RecursiveCharacterTextSplitter"
            }
        }

        db.session.commit()

        return {
            "document_id": document.id,
            "processing_status": document.processing_status,
            "page_count": len(pages),
            "chunk_count": len(chunk_records)
        }

    except Exception as exc:

        db.session.rollback()

        # Re-fetch after rollback before updating failure status.
        failed_document = Document.query.filter_by(
            id=document_id,
            user_id=user_id
        ).first()

        if failed_document is not None:
            failed_document.processing_status = "failed"
            failed_document.processing_error = str(exc)[:2000]

            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

        if isinstance(exc, PDFProcessingError):
            raise

        raise PDFProcessingError(
            "An unexpected error occurred during PDF processing."
        ) from exc
