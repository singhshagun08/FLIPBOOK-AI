
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import User, Document
from app.models.chat import ChatSession, ChatMessage
from flask_jwt_extended import create_access_token


class TestConfig(TestingConfig):
    pass


def create_user(username, email):
    user = User(
        full_name=username,
        username=username,
        email=email
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
            "token_type": "access"
        }
    )


def create_document(user_id, title="Chat Test Document"):
    document = Document(
        user_id=user_id,
        title=title,
        original_filename="chat_test.pdf",
        stored_filename="chat_test_unique.pdf",
        file_path="test_uploads/chat_test_unique.pdf",
        file_size=1024,
        mime_type="application/pdf",
        processing_status="completed"
    )

    db.session.add(document)
    db.session.commit()

    return document


def run_tests():

    app = create_app("testing")

    passed = 0
    failed = 0

    with app.app_context():

        db.create_all()

        try:
            client = app.test_client()

            user = create_user(
                "chat_test_user",
                "chat_test@example.com"
            )

            other_user = create_user(
                "chat_other_user",
                "chat_other@example.com"
            )

            document = create_document(user.id)

            token = create_token(user)
            other_token = create_token(other_user)

            headers = {
                "Authorization": f"Bearer {token}"
            }

            other_headers = {
                "Authorization": f"Bearer {other_token}"
            }

            session_id = None

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
                response = client.get("/api/chat/sessions")
                assert response.status_code == 401

            check(
                "Chat API requires JWT authentication",
                test_auth_required
            )

            # ------------------------------------------------
            # TEST 2: Create chat session
            # ------------------------------------------------

            def test_create_session():
                nonlocal session_id

                response = client.post(
                    "/api/chat/sessions",
                    headers=headers,
                    json={
                        "title": "Machine Learning Research",
                        "description": "Research chat",
                        "document_ids": [document.id]
                    }
                )

                assert response.status_code == 201, (
                    response.get_json()
                )

                result = response.get_json()

                assert result["success"] is True
                assert (
                    result["data"]["title"]
                    == "Machine Learning Research"
                )
                assert (
                    result["data"]["document_ids"]
                    == [document.id]
                )
                assert result["data"]["message_count"] == 0

                session_id = result["data"]["id"]

            check(
                "Create chat session",
                test_create_session
            )

            # ------------------------------------------------
            # TEST 3: Create session with default title
            # ------------------------------------------------

            def test_default_title():
                response = client.post(
                    "/api/chat/sessions",
                    headers=headers,
                    json={}
                )

                assert response.status_code == 201

                result = response.get_json()

                assert (
                    result["data"]["title"]
                    == "New conversation"
                )

            check(
                "Create session with default title",
                test_default_title
            )

            # ------------------------------------------------
            # TEST 4: Reject invalid session title
            # ------------------------------------------------

            def test_invalid_title():
                response = client.post(
                    "/api/chat/sessions",
                    headers=headers,
                    json={"title": "   "}
                )

                assert response.status_code == 400

            check(
                "Reject empty chat session title",
                test_invalid_title
            )

            # ------------------------------------------------
            # TEST 5: Reject invalid document IDs
            # ------------------------------------------------

            def test_invalid_document_ids():
                response = client.post(
                    "/api/chat/sessions",
                    headers=headers,
                    json={"document_ids": "invalid"}
                )

                assert response.status_code == 400

                response = client.post(
                    "/api/chat/sessions",
                    headers=headers,
                    json={"document_ids": [True]}
                )

                assert response.status_code == 400

            check(
                "Reject invalid document IDs",
                test_invalid_document_ids
            )

            # ------------------------------------------------
            # TEST 6: Prevent selecting another user's document
            # ------------------------------------------------

            def test_foreign_document_selection():
                response = client.post(
                    "/api/chat/sessions",
                    headers=other_headers,
                    json={
                        "title": "Unauthorized document test",
                        "document_ids": [document.id]
                    }
                )

                assert response.status_code == 404

            check(
                "Prevent cross-user document selection",
                test_foreign_document_selection
            )

            # ------------------------------------------------
            # TEST 7: List chat sessions
            # ------------------------------------------------

            def test_list_sessions():
                response = client.get(
                    "/api/chat/sessions",
                    headers=headers
                )

                assert response.status_code == 200

                result = response.get_json()

                assert result["success"] is True
                assert (
                    result["data"]["pagination"]["total"]
                    == 2
                )
                assert len(result["data"]["sessions"]) == 2

            check(
                "List chat sessions",
                test_list_sessions
            )

            # ------------------------------------------------
            # TEST 8: Filter archived sessions
            # ------------------------------------------------

            def test_archive_filter():
                response = client.get(
                    "/api/chat/sessions?archived=false",
                    headers=headers
                )

                assert response.status_code == 200

                result = response.get_json()

                assert all(
                    not item["is_archived"]
                    for item in result["data"]["sessions"]
                )

                response = client.get(
                    "/api/chat/sessions?archived=invalid",
                    headers=headers
                )

                assert response.status_code == 400

            check(
                "Filter and validate archived sessions",
                test_archive_filter
            )

            # ------------------------------------------------
            # TEST 9: Pagination validation
            # ------------------------------------------------

            def test_pagination():
                response = client.get(
                    "/api/chat/sessions?page=0",
                    headers=headers
                )

                assert response.status_code == 400

                response = client.get(
                    "/api/chat/sessions?per_page=101",
                    headers=headers
                )

                assert response.status_code == 400

            check(
                "Validate chat session pagination",
                test_pagination
            )

            # ------------------------------------------------
            # TEST 10: Get session details
            # ------------------------------------------------

            def test_get_session():
                response = client.get(
                    f"/api/chat/sessions/{session_id}",
                    headers=headers
                )

                assert response.status_code == 200

                result = response.get_json()

                assert result["success"] is True
                assert result["data"]["id"] == session_id
                assert (
                    result["data"]["title"]
                    == "Machine Learning Research"
                )
                assert result["data"]["messages"] == []

            check(
                "Retrieve chat session details",
                test_get_session
            )

            # ------------------------------------------------
            # TEST 11: Update session title and description
            # ------------------------------------------------

            def test_update_session():
                response = client.put(
                    f"/api/chat/sessions/{session_id}",
                    headers=headers,
                    json={
                        "title": "Updated Research Chat",
                        "description": "Updated description"
                    }
                )

                assert response.status_code == 200

                result = response.get_json()

                assert (
                    result["data"]["title"]
                    == "Updated Research Chat"
                )
                assert (
                    result["data"]["description"]
                    == "Updated description"
                )

            check(
                "Update chat session details",
                test_update_session
            )

            # ------------------------------------------------
            # TEST 12: Archive session
            # ------------------------------------------------

            def test_archive_session():
                response = client.put(
                    f"/api/chat/sessions/{session_id}",
                    headers=headers,
                    json={"is_archived": True}
                )

                assert response.status_code == 200
                assert (
                    response.get_json()["data"]["is_archived"]
                    is True
                )

            check(
                "Archive chat session",
                test_archive_session
            )

            # ------------------------------------------------
            # TEST 13: Update selected documents
            # ------------------------------------------------

            def test_update_documents():
                response = client.put(
                    f"/api/chat/sessions/{session_id}",
                    headers=headers,
                    json={"document_ids": []}
                )

                assert response.status_code == 200
                assert (
                    response.get_json()["data"]["document_ids"]
                    == []
                )

                response = client.put(
                    f"/api/chat/sessions/{session_id}",
                    headers=headers,
                    json={"document_ids": [document.id]}
                )

                assert response.status_code == 200
                assert (
                    response.get_json()["data"]["document_ids"]
                    == [document.id]
                )

            check(
                "Update selected chat documents",
                test_update_documents
            )

            # ------------------------------------------------
            # TEST 14: Reject foreign document update
            # ------------------------------------------------

            def test_foreign_document_update():
                response = client.put(
                    f"/api/chat/sessions/{session_id}",
                    headers=headers,
                    json={"document_ids": [999999]}
                )

                assert response.status_code == 404

            check(
                "Prevent selecting unavailable documents",
                test_foreign_document_update
            )

            # ------------------------------------------------
            # TEST 15: Prevent cross-user session access
            # ------------------------------------------------

            def test_foreign_session_access():
                response = client.get(
                    f"/api/chat/sessions/{session_id}",
                    headers=other_headers
                )

                assert response.status_code == 404

            check(
                "Prevent cross-user session access",
                test_foreign_session_access
            )

            # ------------------------------------------------
            # TEST 16: Prevent cross-user session update
            # ------------------------------------------------

            def test_foreign_session_update():
                response = client.put(
                    f"/api/chat/sessions/{session_id}",
                    headers=other_headers,
                    json={"title": "Unauthorized update"}
                )

                assert response.status_code == 404

            check(
                "Prevent cross-user session update",
                test_foreign_session_update
            )

            # ------------------------------------------------
            # TEST 17: Missing session
            # ------------------------------------------------

            def test_missing_session():
                response = client.get(
                    "/api/chat/sessions/999999",
                    headers=headers
                )

                assert response.status_code == 404

            check(
                "Missing chat session returns 404",
                test_missing_session
            )

            # ------------------------------------------------
            # TEST 18: Create message for cascade test
            # ------------------------------------------------

            def test_create_message():
                message = ChatMessage(
                    chat_session_id=session_id,
                    role="user",
                    content="What is machine learning?"
                )

                db.session.add(message)
                db.session.commit()

                response = client.get(
                    f"/api/chat/sessions/{session_id}",
                    headers=headers
                )

                assert response.status_code == 200

                result = response.get_json()

                assert (
                    result["data"]["message_count"] == 1
                )
                assert len(result["data"]["messages"]) == 1
                assert (
                    result["data"]["messages"][0]["role"]
                    == "user"
                )

            check(
                "Retrieve chat message history",
                test_create_message
            )

            # ------------------------------------------------
            # TEST 19: Prevent cross-user session deletion
            # ------------------------------------------------

            def test_foreign_session_delete():
                response = client.delete(
                    f"/api/chat/sessions/{session_id}",
                    headers=other_headers
                )

                assert response.status_code == 404

            check(
                "Prevent cross-user session deletion",
                test_foreign_session_delete
            )

            # ------------------------------------------------
            # TEST 20: Delete session and verify cascade
            # ------------------------------------------------

            def test_delete_session():
                response = client.delete(
                    f"/api/chat/sessions/{session_id}",
                    headers=headers
                )

                assert response.status_code == 200

                assert db.session.get(
                    ChatSession,
                    session_id
                ) is None

                remaining_messages = ChatMessage.query.filter_by(
                    chat_session_id=session_id
                ).count()

                assert remaining_messages == 0

            check(
                "Delete chat session and its messages",
                test_delete_session
            )

            # ------------------------------------------------
            # RESULTS
            # ------------------------------------------------

            print("\nCHAT API TEST RESULTS")
            print("---------------------------")
            print(f"Passed: {passed}")
            print(f"Failed: {failed}")
            print(f"Total:  {passed + failed}")

        finally:
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    run_tests()
