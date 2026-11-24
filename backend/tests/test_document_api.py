
import tempfile
from io import BytesIO

import fitz

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import User
from flask_jwt_extended import create_access_token


class TestConfig(TestingConfig):
    UPLOAD_FOLDER = "test_uploads"


def create_pdf():
    """Generate a valid two-page PDF for API testing."""
    pdf = fitz.open()

    page = pdf.new_page()
    page.insert_text(
        (72, 72),
        "FLIPBOOK-AI API integration test. "
        "This document tests PDF extraction, "
        "text splitting, and document chunk storage."
    )

    page = pdf.new_page()
    page.insert_text(
        (72, 72),
        "This is the second page of the test document. "
        "It verifies page-level text extraction."
    )

    content = pdf.tobytes()
    pdf.close()

    return content


def create_user(username, email):
    user = User(
        full_name=username,
        username=username,
        email=email,
    )

    user.set_password("TestPassword123!")

    db.session.add(user)
    db.session.commit()

    return user


def create_token(user):
    return create_access_token(
        identity=str(user.id),
        additional_claims={
            "token_version": user.token_version,
            "token_type": "access",
        }
    )


def run_tests():
    with tempfile.TemporaryDirectory() as temp_directory:

        app = create_app("testing")
        app.config["UPLOAD_FOLDER"] = temp_directory

        passed = 0
        failed = 0

        with app.app_context():
            db.create_all()

            try:
                client = app.test_client()

                user = create_user(
                    "api_test_user",
                    "api_test@example.com"
                )

                other_user = create_user(
                    "api_other_user",
                    "api_other@example.com"
                )

                token = create_token(user)
                other_token = create_token(other_user)

                headers = {
                    "Authorization": f"Bearer {token}"
                }

                other_headers = {
                    "Authorization": f"Bearer {other_token}"
                }

                pdf_content = create_pdf()
                document_id = None

                def check(name, test_function):
                    nonlocal passed, failed

                    try:
                        test_function()
                        passed += 1
                        print(f"PASS: {name}")

                    except Exception as exc:
                        failed += 1
                        print(f"FAIL: {name}")
                        print(
                            f"      {type(exc).__name__}: {exc}"
                        )

                # ------------------------------------------------
                # TEST 1: Authentication required
                # ------------------------------------------------

                def test_auth_required():
                    response = client.get("/api/documents")
                    assert response.status_code == 401

                check(
                    "JWT authentication required",
                    test_auth_required
                )

                # ------------------------------------------------
                # TEST 2: Upload document
                # ------------------------------------------------

                def test_upload():
                    nonlocal document_id

                    response = client.post(
                        "/api/documents/upload",
                        headers=headers,
                        data={
                            "file": (
                                BytesIO(pdf_content),
                                "api_sample.pdf"
                            ),
                            "title": "API Test Document",
                            "description": "Integration testing"
                        },
                        content_type="multipart/form-data"
                    )

                    assert response.status_code == 201, (
                        response.get_json()
                    )

                    result = response.get_json()

                    assert result["success"] is True
                    assert (
                        result["data"]["title"]
                        == "API Test Document"
                    )

                    document_id = result["data"]["id"]

                check("Upload PDF API", test_upload)

                # ------------------------------------------------
                # TEST 3: List documents
                # ------------------------------------------------

                def test_list():
                    response = client.get(
                        "/api/documents",
                        headers=headers
                    )

                    assert response.status_code == 200

                    result = response.get_json()

                    assert result["success"] is True
                    assert (
                        len(result["data"]["documents"]) == 1
                    )
                    assert (
                        result["data"]["pagination"]["total"] == 1
                    )

                check("List documents API", test_list)

                # ------------------------------------------------
                # TEST 4: Get document details
                # ------------------------------------------------

                def test_details():
                    response = client.get(
                        f"/api/documents/{document_id}",
                        headers=headers
                    )

                    assert response.status_code == 200

                    result = response.get_json()

                    assert (
                        result["data"]["id"] == document_id
                    )

                check("Get document details API", test_details)

                # ------------------------------------------------
                # TEST 5: Update document
                # ------------------------------------------------

                def test_update():
                    response = client.put(
                        f"/api/documents/{document_id}",
                        headers=headers,
                        json={
                            "title": "Updated API Document",
                            "description": "Updated description",
                            "is_favorite": True
                        }
                    )

                    assert response.status_code == 200

                    result = response.get_json()

                    assert (
                        result["data"]["title"]
                        == "Updated API Document"
                    )
                    assert (
                        result["data"]["is_favorite"] is True
                    )

                check("Update document API", test_update)

                # ------------------------------------------------
                # TEST 6: Download document
                # ------------------------------------------------

                def test_download():
                    response = client.get(
                        f"/api/documents/{document_id}/download",
                        headers=headers
                    )

                    assert response.status_code == 200
                    assert response.mimetype == "application/pdf"
                    assert response.data == pdf_content

                check("Download document API", test_download)

                # ------------------------------------------------
                # TEST 7: Process PDF
                # ------------------------------------------------

                def test_process_document():
                    response = client.post(
                        f"/api/documents/{document_id}/process",
                        headers=headers
                    )

                    assert response.status_code == 200, (
                        response.get_json()
                    )

                    result = response.get_json()

                    assert result["success"] is True

                    assert (
                        result["data"]["processing_status"]
                        == "completed"
                    )

                    assert (
                        result["data"]["page_count"] == 2
                    )

                    assert (
                        result["data"]["chunk_count"] >= 1
                    )

                    assert (
                        result["data"]["extracted_page_count"] == 2
                    )

                check(
                    "Process PDF API",
                    test_process_document
                )

                # ------------------------------------------------
                # TEST 8: Retrieve processing status
                # ------------------------------------------------

                def test_processing_status():
                    response = client.get(
                        f"/api/documents/{document_id}/processing-status",
                        headers=headers
                    )

                    assert response.status_code == 200

                    result = response.get_json()

                    assert result["success"] is True

                    assert (
                        result["data"]["processing_status"]
                        == "completed"
                    )

                    assert (
                        result["data"]["page_count"] == 2
                    )

                    assert (
                        result["data"]["extracted_page_count"] == 2
                    )

                    assert (
                        result["data"]["chunk_count"] >= 1
                    )

                    assert (
                        result["data"]["extraction_engine"]
                        == "PyMuPDF"
                    )

                    assert (
                        result["data"]["text_splitter"]
                        == "LangChain RecursiveCharacterTextSplitter"
                    )

                check(
                    "Get PDF processing status API",
                    test_processing_status
                )

                # ------------------------------------------------
                # TEST 9: Retrieve document chunks
                # ------------------------------------------------

                def test_get_chunks():
                    response = client.get(
                        f"/api/documents/{document_id}/chunks",
                        headers=headers
                    )

                    assert response.status_code == 200

                    result = response.get_json()

                    assert result["success"] is True

                    chunks = result["data"]["chunks"]

                    assert len(chunks) >= 1

                    assert (
                        result["data"]["pagination"]["total"]
                        == len(chunks)
                    )

                    assert all(
                        chunk["document_id"] == document_id
                        for chunk in chunks
                    )

                    assert all(
                        chunk["content"].strip()
                        for chunk in chunks
                    )

                check(
                    "Retrieve document chunks API",
                    test_get_chunks
                )

                # ------------------------------------------------
                # TEST 10: Chunk pagination
                # ------------------------------------------------

                def test_chunk_pagination():
                    response = client.get(
                        f"/api/documents/{document_id}/chunks"
                        "?page=1&per_page=1",
                        headers=headers
                    )

                    assert response.status_code == 200

                    result = response.get_json()

                    assert result["success"] is True

                    assert (
                        len(result["data"]["chunks"]) <= 1
                    )

                    assert (
                        result["data"]["pagination"]["page"] == 1
                    )

                    assert (
                        result["data"]["pagination"]["per_page"] == 1
                    )

                check(
                    "Document chunks pagination API",
                    test_chunk_pagination
                )

                # ------------------------------------------------
                # TEST 11: Invalid chunk pagination
                # ------------------------------------------------

                def test_invalid_chunk_pagination():
                    response = client.get(
                        f"/api/documents/{document_id}/chunks"
                        "?page=0",
                        headers=headers
                    )

                    assert response.status_code == 400

                    response = client.get(
                        f"/api/documents/{document_id}/chunks"
                        "?per_page=101",
                        headers=headers
                    )

                    assert response.status_code == 400

                check(
                    "Reject invalid chunk pagination",
                    test_invalid_chunk_pagination
                )

                # ------------------------------------------------
                # TEST 12: Prevent cross-user document access
                # ------------------------------------------------

                def test_foreign_access():
                    response = client.get(
                        f"/api/documents/{document_id}",
                        headers=other_headers
                    )

                    assert response.status_code == 404

                check(
                    "Prevent cross-user document access",
                    test_foreign_access
                )

                # ------------------------------------------------
                # TEST 13: Prevent unauthorized update
                # ------------------------------------------------

                def test_foreign_update():
                    response = client.put(
                        f"/api/documents/{document_id}",
                        headers=other_headers,
                        json={
                            "title": "Unauthorized change"
                        }
                    )

                    assert response.status_code == 404

                check(
                    "Prevent cross-user document update",
                    test_foreign_update
                )

                # ------------------------------------------------
                # TEST 14: Prevent unauthorized download
                # ------------------------------------------------

                def test_foreign_download():
                    response = client.get(
                        f"/api/documents/{document_id}/download",
                        headers=other_headers
                    )

                    assert response.status_code == 404

                check(
                    "Prevent cross-user document download",
                    test_foreign_download
                )

                # ------------------------------------------------
                # TEST 15: Prevent unauthorized PDF processing
                # ------------------------------------------------

                def test_foreign_processing():
                    response = client.post(
                        f"/api/documents/{document_id}/process",
                        headers=other_headers
                    )

                    assert response.status_code == 404

                check(
                    "Prevent cross-user PDF processing",
                    test_foreign_processing
                )

                # ------------------------------------------------
                # TEST 16: Prevent unauthorized chunk access
                # ------------------------------------------------

                def test_foreign_chunks():
                    response = client.get(
                        f"/api/documents/{document_id}/chunks",
                        headers=other_headers
                    )

                    assert response.status_code == 404

                check(
                    "Prevent cross-user chunk access",
                    test_foreign_chunks
                )

                # ------------------------------------------------
                # TEST 17: Prevent unauthorized status access
                # ------------------------------------------------

                def test_foreign_processing_status():
                    response = client.get(
                        f"/api/documents/{document_id}/processing-status",
                        headers=other_headers
                    )

                    assert response.status_code == 404

                check(
                    "Prevent cross-user processing status access",
                    test_foreign_processing_status
                )

                # ------------------------------------------------
                # TEST 18: Processing endpoint requires JWT
                # ------------------------------------------------

                def test_processing_auth_required():
                    response = client.post(
                        f"/api/documents/{document_id}/process"
                    )

                    assert response.status_code == 401

                check(
                    "PDF processing requires authentication",
                    test_processing_auth_required
                )

                # ------------------------------------------------
                # TEST 19: Missing document
                # ------------------------------------------------

                def test_missing_document():
                    response = client.get(
                        "/api/documents/999999",
                        headers=headers
                    )

                    assert response.status_code == 404

                check(
                    "Missing document returns 404",
                    test_missing_document
                )

                # ------------------------------------------------
                # TEST 20: Delete document
                # ------------------------------------------------

                def test_delete():
                    response = client.delete(
                        f"/api/documents/{document_id}",
                        headers=headers
                    )

                    assert response.status_code == 200

                    result = client.get(
                        f"/api/documents/{document_id}",
                        headers=headers
                    )

                    assert result.status_code == 404

                check("Delete document API", test_delete)

                # ------------------------------------------------
                # TEST 21: Prevent unauthorized deletion
                # ------------------------------------------------

                def test_foreign_delete():
                    response = client.delete(
                        f"/api/documents/{document_id}",
                        headers=other_headers
                    )

                    assert response.status_code == 404

                check(
                    "Prevent cross-user document deletion",
                    test_foreign_delete
                )

                # ------------------------------------------------
                # RESULTS
                # ------------------------------------------------

                print("\nDOCUMENT API TEST RESULTS")
                print("---------------------------")
                print(f"Passed: {passed}")
                print(f"Failed: {failed}")
                print(f"Total:  {passed + failed}")

            finally:
                db.session.remove()
                db.drop_all()


if __name__ == "__main__":
    run_tests()
