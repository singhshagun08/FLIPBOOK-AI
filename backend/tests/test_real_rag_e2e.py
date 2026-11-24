
import gc
import io
import json
import shutil
import tempfile
import time
import uuid
from pathlib import Path

import fitz

from app import create_app
from app.extensions import db


# ============================================================
# CONFIGURATION
# ============================================================

TEST_EMAIL = f"rag_test_{uuid.uuid4().hex[:8]}@example.com"
TEST_USERNAME = f"rag_test_{uuid.uuid4().hex[:8]}"
TEST_PASSWORD = "TestPassword123!"

TEST_QUESTION = (
    "What is the annual research budget of Project Aurora?"
)

EXPECTED_ANSWER = "2.4 million credits"


# ============================================================
# HELPERS
# ============================================================

def check(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"PASS: {message}")


def get_response_body(response):
    body = response.get_json(silent=True)

    if not isinstance(body, dict):
        raise AssertionError(
            f"Expected JSON object. HTTP {response.status_code}: "
            f"{response.get_data(as_text=True)[:2000]}"
        )

    print(
        f"PASS: API returned JSON. "
        f"HTTP status: {response.status_code}"
    )

    return body


def extract_data(response):
    body = get_response_body(response)

    if body.get("success") is not True:
        raise AssertionError(
            "API request failed:\n"
            + json.dumps(body, indent=2, default=str)
        )

    data = body.get("data", {})

    if not isinstance(data, dict):
        raise AssertionError(
            f"Expected data to be a dictionary: {data}"
        )

    print("PASS: API request succeeded")
    return data


def find_id(data, possible_keys=None):
    """
    Extract IDs from direct or nested API response structures.
    """

    if possible_keys is None:
        possible_keys = []

    if isinstance(data, dict):

        for key in possible_keys:
            value = data.get(key)

            if isinstance(value, dict):
                nested_id = value.get("id")

                if (
                    isinstance(nested_id, int)
                    and not isinstance(nested_id, bool)
                ):
                    return nested_id

        direct_id = data.get("id")

        if (
            isinstance(direct_id, int)
            and not isinstance(direct_id, bool)
        ):
            return direct_id

        for value in data.values():
            result = find_id(value, possible_keys)

            if result is not None:
                return result

    elif isinstance(data, list):

        for item in data:
            result = find_id(item, possible_keys)

            if result is not None:
                return result

    return None


def find_nested_value(data, possible_keys):
    """
    Find a named value recursively.
    """

    if isinstance(data, dict):

        for key in possible_keys:
            value = data.get(key)

            if value is not None:
                return value

        for value in data.values():
            result = find_nested_value(value, possible_keys)

            if result is not None:
                return result

    elif isinstance(data, list):

        for item in data:
            result = find_nested_value(item, possible_keys)

            if result is not None:
                return result

    return None


def find_list(data, possible_keys):
    """
    Find a list in a nested API response.
    """

    if isinstance(data, dict):

        for key in possible_keys:
            value = data.get(key)

            if isinstance(value, list):
                return value

        for value in data.values():
            result = find_list(value, possible_keys)

            if result is not None:
                return result

    elif isinstance(data, list):

        for item in data:
            result = find_list(item, possible_keys)

            if result is not None:
                return result

    return None


def extract_answer(data):
    """
    Extract the generated assistant answer.
    """

    answer = find_nested_value(
        data,
        [
            "answer",
            "assistant_response",
            "response"
        ]
    )

    if isinstance(answer, str) and answer.strip():
        return answer

    assistant_message = find_nested_value(
        data,
        ["assistant_message"]
    )

    if isinstance(assistant_message, dict):
        content = assistant_message.get("content")

        if isinstance(content, str) and content.strip():
            return content

    message = find_nested_value(
        data,
        ["message"]
    )

    if isinstance(message, dict):
        content = message.get("content")

        if isinstance(content, str) and content.strip():
            return content

    return None


def create_test_pdf():
    """
    Generate a two-page PDF containing known information.
    """

    pdf = fitz.open()

    page1 = pdf.new_page()

    page1.insert_text(
        (72, 72),
        "Project Aurora Research Report",
        fontsize=18
    )

    page1.insert_text(
        (72, 120),
        (
            "Project Aurora is an experimental research initiative "
            "that began in 2021. Its annual research budget is "
            "2.4 million credits. The project focuses on renewable "
            "energy storage and advanced battery research."
        ),
        fontsize=11
    )

    page2 = pdf.new_page()

    page2.insert_text(
        (72, 72),
        "Project Objectives",
        fontsize=18
    )

    page2.insert_text(
        (72, 120),
        (
            "Project Aurora aims to improve battery efficiency, "
            "reduce energy storage costs, and develop sustainable "
            "energy infrastructure. Its research team evaluates "
            "battery performance and long-term storage reliability."
        ),
        fontsize=11
    )

    pdf_bytes = pdf.tobytes()
    pdf.close()

    return pdf_bytes


def cleanup_chroma(vector_service):
    """
    Attempt to stop ChromaDB resources before deleting its files.

    ChromaDB's internal system access is version-dependent.
    Cleanup failures are reported but do not hide test results.
    """

    if vector_service is None:
        return

    try:
        vector_store = getattr(
            vector_service,
            "vector_store",
            None
        )

        chroma_client = getattr(
            vector_store,
            "_client",
            None
        )

        chroma_system = getattr(
            chroma_client,
            "_system",
            None
        )

        if chroma_system is not None:

            stop_method = getattr(
                chroma_system,
                "stop",
                None
            )

            if callable(stop_method):
                stop_method()
                print("PASS: ChromaDB system stop requested")

    except Exception as cleanup_error:

        print(
            "ChromaDB cleanup warning:",
            cleanup_error
        )


def remove_temporary_directory(temp_root):
    """
    Remove temporary storage with retries for Windows file locks.
    """

    for attempt in range(1, 6):

        try:
            shutil.rmtree(temp_root)

            print(
                "\nTemporary test storage cleaned up."
            )

            return True

        except FileNotFoundError:
            return True

        except OSError as cleanup_error:

            print(
                f"Cleanup attempt {attempt}/5 failed:",
                cleanup_error
            )

            gc.collect()
            time.sleep(1)

    print(
        "\nWARNING: Temporary storage could not be removed "
        "after 5 attempts:"
    )

    print(temp_root)

    return False


# ============================================================
# MAIN INTEGRATION TEST
# ============================================================

def run_test():

    # --------------------------------------------------------
    # CREATE ISOLATED TEST DIRECTORIES
    # --------------------------------------------------------

    temp_root = Path(
        tempfile.mkdtemp(prefix="flipbook_rag_e2e_")
    )

    chroma_directory = temp_root / "chroma"
    upload_directory = temp_root / "uploads"
    generated_directory = temp_root / "generated"

    chroma_directory.mkdir(parents=True, exist_ok=True)
    upload_directory.mkdir(parents=True, exist_ok=True)
    generated_directory.mkdir(parents=True, exist_ok=True)

    app = None
    vector_service = None
    test_passed = False

    print("\nFLIPBOOK-AI REAL RAG INTEGRATION TEST")
    print("=" * 55)

    print("Database: in-memory SQLite")
    print("ChromaDB:", chroma_directory)
    print("Uploads:", upload_directory)
    print("Ollama: http://localhost:11434")

    try:

        # ----------------------------------------------------
        # INITIALIZE FLASK APPLICATION
        # ----------------------------------------------------

        app = create_app("testing")

        app.config["CHROMA_PERSIST_DIRECTORY"] = str(
            chroma_directory
        )

        app.config["UPLOAD_FOLDER"] = str(
            upload_directory
        )

        app.config["GENERATED_FOLDER"] = str(
            generated_directory
        )

        app.config["TESTING"] = True

        with app.app_context():

            db.create_all()

            client = app.test_client()

            # ------------------------------------------------
            # STEP 1: CREATE TEST USER
            # ------------------------------------------------

            print("\nSTEP 1: CREATE TEST USER")

            register_response = client.post(
                "/api/auth/register",
                json={
                    "full_name": "RAG Integration Tester",
                    "username": TEST_USERNAME,
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                },
                headers={
                    "Content-Type": "application/json"
                }
            )

            if register_response.status_code == 404:
                raise RuntimeError(
                    "Registration endpoint not found. "
                    "Check the registered authentication URL."
                )

            register_data = extract_data(register_response)

            user_id = find_id(
                register_data,
                ["user"]
            )

            check(
                user_id is not None,
                f"Test user registered. User ID: {user_id}"
            )

            # ------------------------------------------------
            # STEP 2: LOGIN AND OBTAIN JWT
            # ------------------------------------------------

            print("\nSTEP 2: LOGIN AND CREATE JWT")

            login_response = client.post(
                "/api/auth/login",
                json={
                    "identifier": TEST_EMAIL,
                    "password": TEST_PASSWORD
                },
                headers={
                    "Content-Type": "application/json"
                }
            )

            if login_response.status_code == 404:
                raise RuntimeError(
                    "Login endpoint not found. "
                    "Check the registered authentication URL."
                )

            login_data = extract_data(login_response)

            access_token = find_nested_value(
                login_data,
                ["access_token"]
            )

            check(
                isinstance(access_token, str)
                and bool(access_token),
                "Login API returned an access token"
            )

            auth_headers = {
                "Authorization": f"Bearer {access_token}"
            }

            print(
                "PASS: Valid JWT obtained through login API"
            )

            # ------------------------------------------------
            # STEP 3: CREATE TEST PDF
            # ------------------------------------------------

            print("\nSTEP 3: CREATE TEST PDF")

            pdf_bytes = create_test_pdf()

            check(
                len(pdf_bytes) > 0,
                "Two-page test PDF generated"
            )

            # ------------------------------------------------
            # STEP 4: UPLOAD PDF
            # ------------------------------------------------

            print("\nSTEP 4: UPLOAD PDF")

            upload_response = client.post(
                "/api/documents/upload",
                headers=auth_headers,
                data={
                    "file": (
                        io.BytesIO(pdf_bytes),
                        "project_aurora_report.pdf"
                    ),
                    "title": "Project Aurora Research Report",
                    "description": (
                        "Real RAG integration test document"
                    )
                },
                content_type="multipart/form-data"
            )

            upload_data = extract_data(upload_response)

            document_id = find_id(
                upload_data,
                ["document"]
            )

            check(
                document_id is not None,
                f"PDF uploaded. Document ID: {document_id}"
            )

            # ------------------------------------------------
            # STEP 5: PROCESS PDF AND INDEX VECTORS
            # ------------------------------------------------

            print("\nSTEP 5: PROCESS PDF AND INDEX")

            process_response = client.post(
                f"/api/documents/{document_id}/process",
                headers=auth_headers
            )

            process_data = extract_data(process_response)

            check(
                process_data.get("processing_status") == "completed",
                "PDF extraction and chunking completed"
            )

            check(
                process_data.get("indexing_status") == "completed",
                "ChromaDB vector indexing completed"
            )

            chunk_count = process_data.get("chunk_count", 0)

            check(
                isinstance(chunk_count, int) and chunk_count > 0,
                f"PDF produced {chunk_count} chunks"
            )

            # ------------------------------------------------
            # STEP 6: VERIFY CHROMADB
            # ------------------------------------------------

            print("\nSTEP 6: VERIFY CHROMADB")

            from app.services.vector_store_service import (
                get_vector_store_service
            )

            vector_service = get_vector_store_service()

            indexed = vector_service.vector_store.get(
                where={
                    "$and": [
                        {"user_id": int(user_id)},
                        {"document_id": int(document_id)}
                    ]
                },
                include=["metadatas"]
            )

            vector_ids = indexed.get("ids", [])

            check(
                len(vector_ids) == chunk_count,
                (
                    f"ChromaDB contains {len(vector_ids)} "
                    "document vectors"
                )
            )

            # ------------------------------------------------
            # STEP 7: CREATE CHAT SESSION
            # ------------------------------------------------

            print("\nSTEP 7: CREATE CHAT SESSION")

            session_response = client.post(
                "/api/chat/sessions",
                headers=auth_headers,
                json={
                    "title": "Project Aurora RAG Test",
                    "description": "Real Ollama integration test",
                    "document_ids": [document_id]
                }
            )

            session_data = extract_data(session_response)

            session_id = find_id(
                session_data,
                ["session", "chat_session"]
            )

            check(
                session_id is not None,
                f"Chat session created. ID: {session_id}"
            )

            # ------------------------------------------------
            # STEP 8: ASK REAL RAG QUESTION
            # ------------------------------------------------

            print("\nSTEP 8: ASK REAL RAG QUESTION")

            print("Question:", TEST_QUESTION)
            print("Waiting for Ollama response...")

            message_response = client.post(
                f"/api/chat/sessions/{session_id}/messages",
                headers=auth_headers,
                json={
                    "question": TEST_QUESTION,
                    "top_k": 5
                }
            )

            message_data = extract_data(message_response)

            answer = extract_answer(message_data)

            if not answer:
                raise AssertionError(
                    "RAG response did not contain an answer:\n"
                    + json.dumps(
                        message_data,
                        indent=2,
                        default=str
                    )
                )

            print("\nAI ANSWER:")
            print(answer)

            normalized_answer = " ".join(
                answer.lower().split()
            )

            check(
                "2.4 million" in normalized_answer,
                "AI answer contains the correct research budget"
            )

            # ------------------------------------------------
            # STEP 9: VERIFY CITATIONS
            # ------------------------------------------------

            print("\nSTEP 9: VERIFY CITATIONS")

            sources = find_list(
                message_data,
                ["sources"]
            )

            check(
                isinstance(sources, list) and len(sources) > 0,
                "RAG returned source citations"
            )

            citation_found = False

            for source in sources:

                if not isinstance(source, dict):
                    continue

                source_document_id = source.get("document_id")
                page_number = source.get("page_number")

                citation = source.get("citation")

                if isinstance(citation, dict):

                    if source_document_id is None:
                        source_document_id = citation.get(
                            "document_id"
                        )

                    if page_number is None:
                        page_number = citation.get(
                            "page_number"
                        )

                if (
                    str(source_document_id) == str(document_id)
                    and page_number is not None
                ):
                    citation_found = True
                    break

            check(
                citation_found,
                (
                    "Citation contains the uploaded document "
                    "and page number"
                )
            )

            # ------------------------------------------------
            # STEP 10: VERIFY CHAT HISTORY
            # ------------------------------------------------

            print("\nSTEP 10: VERIFY CHAT HISTORY")

            history_response = client.get(
                f"/api/chat/sessions/{session_id}",
                headers=auth_headers
            )

            history_data = extract_data(history_response)

            messages = find_list(
                history_data,
                ["messages"]
            )

            check(
                isinstance(messages, list) and len(messages) >= 2,
                "User and assistant messages persisted"
            )

            # ------------------------------------------------
            # FINAL REPORT
            # ------------------------------------------------

            print("\n" + "=" * 55)
            print("REAL RAG INTEGRATION TEST COMPLETED")
            print("=" * 55)

            print("User ID:", user_id)
            print("Document ID:", document_id)
            print("Chat Session ID:", session_id)
            print("Chunks:", chunk_count)
            print("Vectors:", len(vector_ids))
            print("Citations:", len(sources))
            print("Messages:", len(messages))

            print("\nRESULT: ALL CHECKS PASSED")

            test_passed = True

    finally:

        # ----------------------------------------------------
        # CLEANUP
        # ----------------------------------------------------

        if app is not None:

            try:
                with app.app_context():

                    db.session.remove()

                    try:
                        db.drop_all()
                    except Exception as cleanup_error:
                        print(
                            "Database cleanup warning:",
                            cleanup_error
                        )

                    try:
                        db.engine.dispose()
                    except Exception as cleanup_error:
                        print(
                            "Database engine cleanup warning:",
                            cleanup_error
                        )

            except Exception as cleanup_error:

                print(
                    "Application cleanup warning:",
                    cleanup_error
                )

        # ----------------------------------------------------
        # RELEASE CHROMADB RESOURCES
        # ----------------------------------------------------

        cleanup_chroma(vector_service)

        vector_service = None

        # Release remaining Python references.
        gc.collect()

        # ----------------------------------------------------
        # REMOVE TEMPORARY STORAGE
        # ----------------------------------------------------

        if test_passed:

            cleanup_success = remove_temporary_directory(
                temp_root
            )

            if not cleanup_success:
                print(
                    "You can manually remove this temporary "
                    "directory after closing processes using it."
                )

        else:

            print(
                "\nTEST FAILED. Temporary storage preserved:"
            )

            print(temp_root)

            print(
                "This directory is separate from your normal "
                "backend/chroma_db."
            )


if __name__ == "__main__":
    run_test()
