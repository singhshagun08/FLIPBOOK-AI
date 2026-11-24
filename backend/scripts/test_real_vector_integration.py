
import sys
import tempfile
import gc
import time
import shutil
from pathlib import Path

# ==================================================
# 1. CONFIGURE PYTHON IMPORT PATH
# ==================================================

BACKEND_DIR = Path(__file__).resolve().parent.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app
from app.extensions import db
from app.models import User, Document, DocumentChunk

from app.services.vector_store_service import (
    VectorStoreService,
    VectorStoreError,
)


# ==================================================
# 2. MAIN INTEGRATION TEST
# ==================================================

def run_integration_test():

    app = create_app("testing")

    with tempfile.TemporaryDirectory(
        prefix="flipbook_vector_test_",
        ignore_cleanup_errors=True,
    ) as temp_dir:

        chroma_directory = Path(temp_dir) / "chroma"

        app.config["CHROMA_PERSIST_DIRECTORY"] = str(
            chroma_directory
        )

        vector_service = None
        test_successful = False

        with app.app_context():

            print("\n====================================")
            print(" FLIPBOOK-AI REAL VECTOR INTEGRATION")
            print("====================================\n")

            try:

                # ----------------------------------
                # STEP 1: DATABASE INITIALIZATION
                # ----------------------------------

                db.create_all()

                print("[1/7] Temporary database initialized.")

                # ----------------------------------
                # STEP 2: CREATE TEST USERS
                # ----------------------------------

                user1 = User(
                    full_name="Vector Test User",
                    username="vector_test_user",
                    email="vector_test@example.com",
                    password_hash="test-password-hash",
                )

                user2 = User(
                    full_name="Second Test User",
                    username="vector_test_user2",
                    email="vector_test2@example.com",
                    password_hash="test-password-hash",
                )

                db.session.add_all([user1, user2])
                db.session.flush()

                document = Document(
                    user_id=user1.id,
                    title="Artificial Intelligence Research",
                    original_filename="ai_research.pdf",
                    stored_filename="ai_research_test.pdf",
                    file_path="temporary/ai_research_test.pdf",
                    mime_type="application/pdf",
                    file_size=2000,
                    page_count=2,
                    processing_status="completed",
                )

                db.session.add(document)
                db.session.flush()

                document_id = document.id
                user1_id = user1.id
                user2_id = user2.id

                db.session.commit()

                print("[2/7] Test users and document created.")

                # ----------------------------------
                # STEP 3: CREATE DOCUMENT CHUNKS
                # ----------------------------------

                chunks = [
                    DocumentChunk(
                        user_id=user1_id,
                        document_id=document_id,
                        chunk_index=0,
                        page_number=1,
                        content=(
                            "Artificial intelligence enables "
                            "machines to perform tasks that "
                            "normally require human intelligence."
                        ),
                        token_count=20,
                    ),

                    DocumentChunk(
                        user_id=user1_id,
                        document_id=document_id,
                        chunk_index=1,
                        page_number=1,
                        content=(
                            "Machine learning is a branch of "
                            "artificial intelligence that allows "
                            "systems to learn patterns from data."
                        ),
                        token_count=20,
                    ),

                    DocumentChunk(
                        user_id=user1_id,
                        document_id=document_id,
                        chunk_index=2,
                        page_number=2,
                        content=(
                            "Deep learning uses neural networks "
                            "with multiple layers to learn complex "
                            "representations."
                        ),
                        token_count=18,
                    ),
                ]

                db.session.add_all(chunks)
                db.session.commit()

                print("[3/7] Three document chunks created.")

                # ----------------------------------
                # STEP 4: INITIALIZE CHROMADB
                # ----------------------------------

                vector_service = VectorStoreService()

                print("[4/7] ChromaDB initialized.")

                print(
                    "Collection:",
                    vector_service.collection_name,
                )

                print(
                    "Storage:",
                    vector_service.persist_directory,
                )

                # ----------------------------------
                # STEP 5: REAL OLLAMA EMBEDDINGS
                # ----------------------------------

                print(
                    "\nGenerating real embeddings using Ollama..."
                )

                indexing_result = (
                    vector_service.index_document(
                        document_id=document_id,
                        user_id=user1_id,
                    )
                )

                print("\nIndexing successful:")
                print(indexing_result)

                vector_count = (
                    vector_service.vector_store
                    ._collection.count()
                )

                print(
                    "ChromaDB vector count:",
                    vector_count,
                )

                assert vector_count == 3, (
                    f"Expected 3 vectors, got {vector_count}"
                )

                # ----------------------------------
                # STEP 6: REAL SEMANTIC SEARCH
                # ----------------------------------

                print("\nPerforming semantic search...")

                search_results = vector_service.search(
                    query=(
                        "How do computers learn patterns "
                        "from information?"
                    ),
                    user_id=user1_id,
                    top_k=3,
                )

                assert len(search_results) > 0, (
                    "Semantic search returned no results."
                )

                print("\nSearch results:")

                for index, result in enumerate(
                    search_results,
                    start=1,
                ):

                    print(f"\nResult {index}")

                    print(
                        "Content:",
                        result["content"],
                    )

                    print(
                        "Metadata:",
                        result["metadata"],
                    )

                    print(
                        "Distance:",
                        result["distance"],
                    )

                print("\n[6/7] Semantic search successful.")

                # ----------------------------------
                # STEP 7: USER ISOLATION
                # ----------------------------------

                print("\nTesting user-level isolation...")

                user2_results = vector_service.search(
                    query="Artificial intelligence",
                    user_id=user2_id,
                    top_k=3,
                )

                assert len(user2_results) == 0, (
                    "User isolation failed. "
                    "Another user's vectors were returned."
                )

                print(
                    "User isolation successful."
                )

                # ----------------------------------
                # VERIFY SQLITE REFERENCES
                # ----------------------------------

                saved_chunks = (
                    DocumentChunk.query
                    .filter_by(
                        document_id=document_id,
                        user_id=user1_id,
                    )
                    .all()
                )

                assert len(saved_chunks) == 3

                assert all(
                    chunk.embedding_id
                    for chunk in saved_chunks
                ), (
                    "Some embedding IDs were not saved."
                )

                print(
                    "SQLite embedding references verified."
                )

                test_successful = True

                print("\n====================================")
                print(" ALL INTEGRATION CHECKS PASSED")
                print("====================================")

            except Exception:

                db.session.rollback()

                print("\nINTEGRATION TEST FAILED.")

                raise

            finally:

                # ==================================
                # CHROMADB RESOURCE CLEANUP
                # ==================================

                if vector_service is not None:

                    try:

                        vector_store = (
                            vector_service.vector_store
                        )

                        client = getattr(
                            vector_store,
                            "_client",
                            None,
                        )

                        # Stop ChromaDB's internal system.
                        system = getattr(
                            client,
                            "_system",
                            None,
                        )

                        if system is not None:

                            try:
                                system.stop()

                            except Exception as exc:
                                print(
                                    "ChromaDB shutdown warning:",
                                    exc,
                                )

                        # Release references.
                        del vector_store
                        del client

                        vector_service = None

                    except Exception as exc:

                        print(
                            "Resource cleanup warning:",
                            exc,
                        )

                # Force Python garbage collection.
                gc.collect()

                # Remove database session and tables.
                db.session.remove()
                db.drop_all()

                print(
                    "\nTemporary database cleaned up."
                )

        # ==========================================
        # TEMPORARY DIRECTORY CLEANUP
        # ==========================================

        gc.collect()

        if test_successful:
            print(
                "\nIntegration test completed successfully."
            )
        else:
            print(
                "\nIntegration test did not complete successfully."
            )


# ==================================================
# 3. EXECUTION ENTRY POINT
# ==================================================

if __name__ == "__main__":
    run_integration_test()
