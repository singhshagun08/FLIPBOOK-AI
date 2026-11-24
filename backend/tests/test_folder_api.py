
from io import BytesIO
import tempfile

import fitz

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import User, Document
from flask_jwt_extended import create_access_token


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
                    "folder_api_user",
                    "folder_api@example.com"
                )

                other_user = create_user(
                    "folder_api_other",
                    "folder_api_other@example.com"
                )

                headers = {
                    "Authorization": f"Bearer {create_token(user)}"
                }

                other_headers = {
                    "Authorization": f"Bearer {create_token(other_user)}"
                }

                root_id = None
                child_id = None
                grandchild_id = None

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

                # 1. JWT authentication.
                def test_authentication():
                    response = client.get("/api/folders")
                    assert response.status_code == 401

                check("JWT authentication required", test_authentication)

                # 2. Create root folder.
                def test_create_root():
                    nonlocal root_id

                    response = client.post(
                        "/api/folders",
                        headers=headers,
                        json={
                            "name": "Research",
                            "description": "Research materials",
                            "color": "#2563eb"
                        }
                    )

                    assert response.status_code == 201, response.get_json()

                    result = response.get_json()
                    root_id = result["data"]["id"]

                    assert result["data"]["name"] == "Research"
                    assert result["data"]["parent_folder_id"] is None

                check("Create root folder API", test_create_root)

                # 3. Create nested folder.
                def test_create_child():
                    nonlocal child_id

                    response = client.post(
                        "/api/folders",
                        headers=headers,
                        json={
                            "name": "Machine Learning",
                            "parent_folder_id": root_id
                        }
                    )

                    assert response.status_code == 201, response.get_json()

                    child_id = response.get_json()["data"]["id"]

                    assert (
                        response.get_json()["data"]["parent_folder_id"]
                        == root_id
                    )

                check("Create nested folder API", test_create_child)

                # 4. Create grandchild folder.
                def test_create_grandchild():
                    nonlocal grandchild_id

                    response = client.post(
                        "/api/folders",
                        headers=headers,
                        json={
                            "name": "Deep Learning",
                            "parent_folder_id": child_id
                        }
                    )

                    assert response.status_code == 201, response.get_json()
                    grandchild_id = response.get_json()["data"]["id"]

                check("Create grandchild folder API", test_create_grandchild)

                # 5. List root folders.
                def test_list_root():
                    response = client.get(
                        "/api/folders",
                        headers=headers
                    )

                    assert response.status_code == 200

                    folders = response.get_json()["data"]["folders"]

                    assert len(folders) == 1
                    assert folders[0]["name"] == "Research"

                check("List root folders API", test_list_root)

                # 6. List child folders.
                def test_list_children():
                    response = client.get(
                        f"/api/folders?parent_folder_id={root_id}",
                        headers=headers
                    )

                    assert response.status_code == 200

                    folders = response.get_json()["data"]["folders"]

                    assert len(folders) == 1
                    assert folders[0]["name"] == "Machine Learning"

                check("List nested folders API", test_list_children)

                # 7. Get folder details.
                def test_details():
                    response = client.get(
                        f"/api/folders/{root_id}",
                        headers=headers
                    )

                    assert response.status_code == 200

                    result = response.get_json()["data"]

                    assert result["id"] == root_id
                    assert len(result["children"]) == 1

                check("Get folder details API", test_details)

                # 8. Rename folder.
                def test_rename():
                    response = client.put(
                        f"/api/folders/{child_id}",
                        headers=headers,
                        json={"name": "AI Research"}
                    )

                    assert response.status_code == 200
                    assert (
                        response.get_json()["data"]["name"]
                        == "AI Research"
                    )

                check("Rename folder API", test_rename)

                # 9. Move folder to root.
                def test_move_to_root():
                    response = client.put(
                        f"/api/folders/{grandchild_id}",
                        headers=headers,
                        json={"parent_folder_id": None}
                    )

                    assert response.status_code == 200
                    assert (
                        response.get_json()["data"]["parent_folder_id"]
                        is None
                    )

                check("Move folder to root API", test_move_to_root)

                # 10. Reject circular hierarchy.
                def test_circular_hierarchy():
                    response = client.put(
                        f"/api/folders/{root_id}",
                        headers=headers,
                        json={"parent_folder_id": child_id}
                    )

                    assert response.status_code == 400

                check("Prevent circular hierarchy API", test_circular_hierarchy)

                # 11. Reject foreign folder access.
                def test_foreign_access():
                    response = client.get(
                        f"/api/folders/{root_id}",
                        headers=other_headers
                    )

                    assert response.status_code == 404

                check("Prevent cross-user folder access", test_foreign_access)

                # 12. Reject foreign parent folder.
                def test_foreign_parent():
                    response = client.post(
                        "/api/folders",
                        headers=other_headers,
                        json={"name": "Unauthorized Child", "parent_folder_id": root_id}
                    )

                    assert response.status_code == 400

                check("Prevent cross-user parent assignment", test_foreign_parent)

                # 13. Reject empty folder name.
                def test_empty_name():
                    response = client.post(
                        "/api/folders",
                        headers=headers,
                        json={"name": "   "}
                    )

                    assert response.status_code == 400

                check("Reject empty folder name API", test_empty_name)

                # 14. Preserve documents during folder deletion.
                def test_document_preservation():
                    pdf = fitz.open()
                    pdf.new_page()
                    pdf_bytes = pdf.tobytes()
                    pdf.close()

                    folder_response = client.post(
                        "/api/folders",
                        headers=headers,
                        json={"name": "Document Preservation Test"}
                    )

                    folder_id = folder_response.get_json()["data"]["id"]

                    from app.models import Folder

                    folder = db.session.get(Folder, folder_id)

                    document = Document(
                        user_id=user.id,
                        folder_id=folder.id,
                        title="Preserved Document",
                        original_filename="preserved.pdf",
                        stored_filename="preserved-test.pdf",
                        file_path="unused-test-path",
                        mime_type="application/pdf",
                        file_size=len(pdf_bytes),
                        page_count=1,
                        processing_status="pending",
                        checksum="b" * 64
                    )

                    db.session.add(document)
                    db.session.commit()

                    document_id = document.id

                    response = client.delete(
                        f"/api/folders/{folder_id}",
                        headers=headers
                    )

                    assert response.status_code == 200

                    preserved = db.session.get(Document, document_id)

                    assert preserved is not None
                    assert preserved.folder_id is None

                check(
                    "Preserve documents when deleting folder",
                    test_document_preservation
                )

                # 15. Delete folder.
                def test_delete():
                    folder_response = client.post(
                        "/api/folders",
                        headers=headers,
                        json={"name": "Delete Me"}
                    )

                    folder_id = folder_response.get_json()["data"]["id"]

                    response = client.delete(
                        f"/api/folders/{folder_id}",
                        headers=headers
                    )

                    assert response.status_code == 200

                    details = client.get(
                        f"/api/folders/{folder_id}",
                        headers=headers
                    )

                    assert details.status_code == 404

                check("Delete folder API", test_delete)

                print("\nFOLDER API TEST RESULTS")
                print(f"Passed: {passed}")
                print(f"Failed: {failed}")
                print(f"Total:  {passed + failed}")

            finally:
                db.session.remove()
                db.drop_all()


if __name__ == "__main__":
    run_tests()
