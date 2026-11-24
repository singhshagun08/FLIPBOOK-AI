
from pathlib import Path
from tempfile import TemporaryDirectory

import fitz

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import User, Document, DocumentChunk

from app.services.pdf_processing_service import (
    process_document,
    PDFProcessingError,
)


class TestConfig(TestingConfig):
    TESTING = True


def create_test_pdf(path):
    """Create a two-page text-based PDF."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with fitz.open() as pdf:
        page1 = pdf.new_page()
        page1.insert_text(
            (72, 72),
            "This is page one of the FLIPBOOK AI test. " * 100
        )

        page2 = pdf.new_page()
        page2.insert_text(
            (72, 72),
            "This is page two of the FLIPBOOK AI test. " * 100
        )

        pdf.save(path)


def create_test_user():
    """Create a test user."""

    user = User(
        full_name="PDF Processing Test User",
        username="pdf_processing_test_user",
        email="pdf_processing_test@example.com",
    )

    user.set_password("TestPassword123!")

    db.session.add(user)
    db.session.commit()

    return user


def create_test_document(user, pdf_path):
    """Create a document record pointing to the test PDF."""

    pdf_path = Path(pdf_path)

    document = Document(
        user_id=user.id,
        title="PDF Processing Test",
        original_filename="processing_test.pdf",
        stored_filename="processing_test.pdf",
        file_path=str(pdf_path),
        mime_type="application/pdf",
        file_size=pdf_path.stat().st_size,
        page_count=2,
        processing_status="pending",
        extracted_metadata={},
        checksum="test_pdf_processing_checksum",
    )

    db.session.add(document)
    db.session.commit()

    return document


def run_tests():
    passed = 0
    failed = 0

    with TemporaryDirectory() as temp_dir:

        temp_path = Path(temp_dir)

        app = create_app("testing")
        app.config.from_object(TestConfig)

        # Use an isolated upload directory.
        upload_root = temp_path / "uploads"
        app.config["UPLOAD_FOLDER"] = str(upload_root)

        with app.app_context():

            db.create_all()

            try:
                # Create test user.
                user = create_test_user()
                user_id = user.id

                # Match the storage structure used by the service.
                user_directory = upload_root / f"user_{user_id}"
                user_directory.mkdir(
                    parents=True,
                    exist_ok=True
                )

                # Generate PDF inside the permitted user directory.
                pdf_path = user_directory / "processing_test.pdf"

                create_test_pdf(pdf_path)

                # Register document.
                document = create_test_document(
                    user,
                    pdf_path
                )

                document_id = document.id

                def check(name, test_function):
                    nonlocal passed, failed

                    try:
                        db.session.rollback()
                        test_function()

                        passed += 1
                        print(f"PASS: {name}")

                    except Exception as exc:
                        failed += 1
                        db.session.rollback()

                        print(f"FAIL: {name}")
                        print(
                            f"      {type(exc).__name__}: {exc}"
                        )

                # ------------------------------------------------
                # TEST 1: Successful PDF processing
                # ------------------------------------------------

                def test_successful_processing():

                    result = process_document(
                        document_id,
                        user_id,
                        chunk_size=500,
                        chunk_overlap=100
                    )

                    assert result["document_id"] == document_id
                    assert result["processing_status"] == "completed"
                    assert result["page_count"] == 2
                    assert result["chunk_count"] >= 2

                    refreshed = db.session.get(
                        Document,
                        document_id
                    )

                    assert refreshed.processing_status == "completed"

                    metadata = refreshed.extracted_metadata

                    assert metadata is not None
                    assert metadata["extraction"]["chunk_count"] == (
                        result["chunk_count"]
                    )

                check(
                    "Successful PDF processing",
                    test_successful_processing
                )

                # ------------------------------------------------
                # TEST 2: Chunk persistence and metadata
                # ------------------------------------------------

                def test_chunks_saved():

                    chunks = DocumentChunk.query.filter_by(
                        document_id=document_id,
                        user_id=user_id
                    ).order_by(
                        DocumentChunk.chunk_index
                    ).all()

                    assert len(chunks) >= 2

                    assert all(
                        chunk.content.strip()
                        for chunk in chunks
                    )

                    assert all(
                        chunk.page_number in (1, 2)
                        for chunk in chunks
                    )

                    assert all(
                        chunk.token_count > 0
                        for chunk in chunks
                    )

                    assert all(
                        chunk.chunk_metadata is not None
                        for chunk in chunks
                    )

                    indexes = [
                        chunk.chunk_index
                        for chunk in chunks
                    ]

                    assert indexes == list(range(len(chunks)))

                    # Verify that both source pages are represented.
                    page_numbers = {
                        chunk.page_number
                        for chunk in chunks
                    }

                    assert page_numbers == {1, 2}

                check(
                    "Chunk persistence and metadata",
                    test_chunks_saved
                )

                # ------------------------------------------------
                # TEST 3: Reprocessing without duplicate chunks
                # ------------------------------------------------

                def test_reprocessing():

                    first_chunks = DocumentChunk.query.filter_by(
                        document_id=document_id,
                        user_id=user_id
                    ).order_by(
                        DocumentChunk.chunk_index
                    ).all()

                    first_count = len(first_chunks)

                    first_content = [
                        chunk.content
                        for chunk in first_chunks
                    ]

                    result = process_document(
                        document_id,
                        user_id,
                        chunk_size=500,
                        chunk_overlap=100
                    )

                    second_chunks = DocumentChunk.query.filter_by(
                        document_id=document_id,
                        user_id=user_id
                    ).order_by(
                        DocumentChunk.chunk_index
                    ).all()

                    second_count = len(second_chunks)

                    second_content = [
                        chunk.content
                        for chunk in second_chunks
                    ]

                    assert first_count == second_count
                    assert first_content == second_content
                    assert result["chunk_count"] == second_count

                    # Verify unique chunk indexes.
                    indexes = [
                        chunk.chunk_index
                        for chunk in second_chunks
                    ]

                    assert len(indexes) == len(set(indexes))

                check(
                    "Reprocessing without duplicate chunks",
                    test_reprocessing
                )

                # ------------------------------------------------
                # TEST 4: Document ownership protection
                # ------------------------------------------------

                def test_wrong_user():

                    try:
                        process_document(
                            document_id,
                            user_id + 9999
                        )

                    except PDFProcessingError as exc:

                        assert "not found" in str(exc).lower()
                        return

                    raise AssertionError(
                        "Unauthorized document processing was allowed."
                    )

                check(
                    "Document ownership protection",
                    test_wrong_user
                )

                # ------------------------------------------------
                # TEST 5: Missing PDF failure handling
                # ------------------------------------------------

                def test_missing_file():

                    broken_path = (
                        user_directory / "missing.pdf"
                    )

                    document = db.session.get(
                        Document,
                        document_id
                    )

                    document.file_path = str(broken_path)
                    db.session.commit()

                    try:
                        process_document(
                            document_id,
                            user_id
                        )

                    except PDFProcessingError:
                        pass

                    else:
                        raise AssertionError(
                            "Missing PDF file was processed."
                        )

                    db.session.expire_all()

                    refreshed = db.session.get(
                        Document,
                        document_id
                    )

                    assert refreshed.processing_status == "failed"
                    assert refreshed.processing_error is not None

                    # Previous successful chunks should remain intact.
                    assert DocumentChunk.query.filter_by(
                        document_id=document_id,
                        user_id=user_id
                    ).count() > 0

                check(
                    "Processing failure handling",
                    test_missing_file
                )

                # ------------------------------------------------
                # FINAL RESULTS
                # ------------------------------------------------

                print("\nPDF PROCESSING TEST RESULTS")
                print("---------------------------")
                print(f"Passed: {passed}")
                print(f"Failed: {failed}")
                print(f"Total:  {passed + failed}")

            finally:
                db.session.remove()
                db.drop_all()


if __name__ == "__main__":
    run_tests()
