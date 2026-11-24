
import tempfile

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import User, Folder, Document
from app.services.folder_service import (
    create_folder,
    list_folders,
    get_folder_details,
    update_folder,
    delete_folder,
    FolderServiceError,
)


class TestConfig(TestingConfig):
    UPLOAD_FOLDER = "test_uploads"


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


def run_tests():
    app = create_app("testing")

    passed = 0
    failed = 0

    with app.app_context():
        db.create_all()

        try:
            user = create_user(
                "folder_test_user",
                "folder_test@example.com"
            )

            other_user = create_user(
                "folder_other_user",
                "folder_other@example.com"
            )

            root_folder = None
            child_folder = None
            grandchild_folder = None

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

            # 1. Create root folder.
            def test_create_root():
                nonlocal root_folder

                root_folder = create_folder(
                    user_id=user.id,
                    name="Research",
                    description="Research documents",
                    color="#2563eb"
                )

                assert root_folder.id is not None
                assert root_folder.parent_folder_id is None

            check("Create root folder", test_create_root)

            # 2. Create nested folder.
            def test_create_child():
                nonlocal child_folder

                child_folder = create_folder(
                    user_id=user.id,
                    name="Machine Learning",
                    parent_folder_id=root_folder.id
                )

                assert child_folder.parent_folder_id == root_folder.id

            check("Create nested folder", test_create_child)

            # 3. Create grandchild folder.
            def test_create_grandchild():
                nonlocal grandchild_folder

                grandchild_folder = create_folder(
                    user_id=user.id,
                    name="Deep Learning",
                    parent_folder_id=child_folder.id
                )

                assert grandchild_folder.parent_folder_id == child_folder.id

            check("Create grandchild folder", test_create_grandchild)

            # 4. List root folders.
            def test_list_root():
                folders = list_folders(user.id)

                assert len(folders) == 1
                assert folders[0].name == "Research"

            check("List root folders", test_list_root)

            # 5. List child folders.
            def test_list_children():
                folders = list_folders(
                    user.id,
                    parent_folder_id=root_folder.id
                )

                assert len(folders) == 1
                assert folders[0].name == "Machine Learning"

            check("List nested folders", test_list_children)

            # 6. Get folder details.
            def test_get_details():
                folder = get_folder_details(
                    root_folder.id,
                    user.id
                )

                assert folder.id == root_folder.id
                assert len(folder.children) == 1

            check("Get folder details", test_get_details)

            # 7. Rename folder.
            def test_rename():
                folder = update_folder(
                    folder_id=child_folder.id,
                    user_id=user.id,
                    name="AI Research"
                )

                assert folder.name == "AI Research"

            check("Rename folder", test_rename)

            # 8. Move folder to root.
            def test_move_to_root():
                folder = update_folder(
                    folder_id=grandchild_folder.id,
                    user_id=user.id,
                    parent_folder_id=None
                )

                assert folder.parent_folder_id is None

            check("Move folder to root", test_move_to_root)

            # 9. Prevent self-parenting.
            def test_self_parent():
                try:
                    update_folder(
                        folder_id=root_folder.id,
                        user_id=user.id,
                        parent_folder_id=root_folder.id
                    )
                except FolderServiceError:
                    return

                raise AssertionError("Self-parenting was allowed.")

            check("Prevent self-parenting", test_self_parent)

            # 10. Prevent circular hierarchy.
            def test_circular_hierarchy():
                try:
                    update_folder(
                        folder_id=root_folder.id,
                        user_id=user.id,
                        parent_folder_id=child_folder.id
                    )
                except FolderServiceError:
                    return

                raise AssertionError("Circular hierarchy was allowed.")

            check("Prevent circular hierarchy", test_circular_hierarchy)

            # 11. Prevent foreign parent access.
            def test_foreign_parent():
                foreign_folder = create_folder(
                    user_id=other_user.id,
                    name="Private Folder"
                )

                try:
                    create_folder(
                        user_id=user.id,
                        name="Unauthorized Child",
                        parent_folder_id=foreign_folder.id
                    )
                except FolderServiceError:
                    return

                raise AssertionError("Foreign parent was accepted.")

            check("Prevent foreign parent access", test_foreign_parent)

            # 12. Reject empty folder name.
            def test_empty_name():
                try:
                    create_folder(
                        user_id=user.id,
                        name="   "
                    )
                except FolderServiceError:
                    return

                raise AssertionError("Empty folder name was accepted.")

            check("Reject empty folder name", test_empty_name)

            # 13. Preserve documents when deleting folder.
            def test_delete_preserves_documents():
                folder = create_folder(
                    user_id=user.id,
                    name="Temporary Folder"
                )

                document = Document(
                    user_id=user.id,
                    folder_id=folder.id,
                    title="Preserved Document",
                    original_filename="preserved.pdf",
                    stored_filename="test-preserved.pdf",
                    file_path="test_uploads/test-preserved.pdf",
                    mime_type="application/pdf",
                    file_size=100,
                    page_count=1,
                    processing_status="pending",
                    checksum="a" * 64
                )

                db.session.add(document)
                db.session.commit()

                document_id = document.id

                delete_folder(folder.id, user.id)

                preserved = db.session.get(Document, document_id)

                assert preserved is not None
                assert preserved.folder_id is None

            check(
                "Delete folder while preserving documents",
                test_delete_preserves_documents
            )

            # 14. Delete folder.
            def test_delete_folder():
                folder = create_folder(
                    user_id=user.id,
                    name="Delete Me"
                )

                delete_folder(folder.id, user.id)

                assert db.session.get(Folder, folder.id) is None

            check("Delete folder", test_delete_folder)

            # 15. Prevent foreign folder access.
            def test_foreign_folder_details():
                foreign_folder = create_folder(
                    user_id=other_user.id,
                    name="Another Private Folder"
                )

                try:
                    get_folder_details(
                        foreign_folder.id,
                        user.id
                    )
                except FolderServiceError:
                    return

                raise AssertionError("Foreign folder was accessible.")

            check("Prevent foreign folder access", test_foreign_folder_details)

            print("\nFOLDER SERVICE TEST RESULTS")
            print(f"Passed: {passed}")
            print(f"Failed: {failed}")
            print(f"Total:  {passed + failed}")

        finally:
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    run_tests()
