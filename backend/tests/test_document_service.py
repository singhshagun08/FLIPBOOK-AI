
from io import BytesIO

import fitz

from werkzeug.datastructures import FileStorage

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import User, Document, Folder
from app.services.document_service import (
    upload_document,
    DocumentServiceError,
)
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import User, Document, Folder
from app.services.document_service import (
    upload_document,
    DocumentServiceError,
)


class TestConfig(TestingConfig):
    UPLOAD_FOLDER = "test_uploads"


def create_test_pdf():
    """Generate a small valid PDF in memory."""
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "FLIPBOOK-AI test document")

    content = pdf.tobytes()
    pdf.close()

    return content


def make_upload(content, filename):
    return FileStorage(
        stream=BytesIO(content),
        filename=filename,
        content_type="application/pdf",
    )


def run_tests():
    app = create_app("testing")
    app.config.from_object(TestConfig)

    passed = 0
    failed = 0

    with app.app_context():
        db.create_all()

        try:
            # Create test users.
            user = User(
                full_name="Test User",
                username="document_test_user",
                email="document_test@example.com",
            )
            user.set_password("TestPassword123!")
            db.session.add(user)

            other_user = User(
                full_name="Other User",
                username="document_test_other",
                email="document_other@example.com",
            )
            other_user.set_password("TestPassword123!")
            db.session.add(other_user)

            db.session.commit()

            pdf_content = create_test_pdf()

            def check(name, test_function):
                nonlocal passed, failed

                try:
                    test_function()
                    passed += 1
                    print(f"PASS: {name}")

                except Exception as exc:
                    failed += 1
                    print(f"FAIL: {name}")
                    print(f"      {type(exc).__name__}: {exc}")

                    db.session.rollback()

            # Test 1: Valid PDF upload.
            def test_valid_upload():
                document = upload_document(
                    make_upload(pdf_content, "sample.pdf"),
                    user.id,
                )

                assert document.id is not None
                assert document.page_count == 1
                assert document.file_size == len(pdf_content)
                assert document.processing_status == "pending"

            check("Valid PDF upload", test_valid_upload)

            # Test 2: Metadata extraction.
            def test_metadata():
                document = Document.query.filter_by(
                    user_id=user.id
                ).first()

                assert document is not None
                assert document.extracted_metadata is not None
                assert not document.extracted_metadata.get("title")

            check("Metadata extraction", test_metadata)

            # Test 3: Duplicate detection.
            def test_duplicate():
                upload_document(
                    make_upload(pdf_content, "duplicate.pdf"),
                    user.id,
                )

            def duplicate_check():
                try:
                    test_duplicate()
                except DocumentServiceError as exc:
                    assert "already been uploaded" in str(exc)
                    return

                raise AssertionError("Duplicate upload was accepted.")

            check("Duplicate detection", duplicate_check)

            # Test 4: Invalid PDF content.
            def test_invalid_pdf():
                upload_document(
                    make_upload(b"This is not a PDF", "invalid.pdf"),
                    user.id,
                )

            def invalid_pdf_check():
                try:
                    test_invalid_pdf()
                except DocumentServiceError as exc:
                    assert "valid readable PDF" in str(exc)
                    return

                raise AssertionError("Invalid PDF was accepted.")

            check("Invalid PDF rejection", invalid_pdf_check)

            # Test 5: Non-PDF extension.
            def test_non_pdf():
                upload_document(
                    make_upload(pdf_content, "sample.txt"),
                    user.id,
                )

            def non_pdf_check():
                try:
                    test_non_pdf()
                except DocumentServiceError as exc:
                    assert "Only PDF files" in str(exc)
                    return

                raise AssertionError("Non-PDF file was accepted.")

            check("Non-PDF extension rejection", non_pdf_check)

            # Test 6: Foreign folder protection.
            def test_foreign_folder():
                folder = Folder(
                    user_id=other_user.id,
                    name="Private Folder",
                )
                db.session.add(folder)
                db.session.commit()

                upload_document(
                    make_upload(pdf_content, "private.pdf"),
                    user.id,
                    folder_id=folder.id,
                )

            def foreign_folder_check():
                try:
                    test_foreign_folder()
                except DocumentServiceError as exc:
                    assert "access denied" in str(exc)
                    return

                raise AssertionError(
                    "Upload into another user's folder was accepted."
                )

            check("Foreign folder protection", foreign_folder_check)

            print("\nDOCUMENT SERVICE TEST RESULTS")
            print(f"Passed: {passed}")
            print(f"Failed: {failed}")
            print(f"Total:  {passed + failed}")

        finally:
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    run_tests()
