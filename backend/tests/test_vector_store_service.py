
import pytest
from unittest.mock import MagicMock

from app import create_app
from app.extensions import db
from app.models import User, Document, DocumentChunk
from app.services.vector_store_service import (
    VectorStoreService,
    VectorStoreError,
)


@pytest.fixture
def app(tmp_path):
    app = create_app("testing")

    app.config["CHROMA_PERSIST_DIRECTORY"] = str(
        tmp_path / "chroma_test"
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def setup_data(app):
    with app.app_context():
        user1 = User(
            full_name="Test User One",
            username="testuser1",
            email="test1@example.com",
            password_hash="test-password-hash",
        )

        user2 = User(
            full_name="Test User Two",
            username="testuser2",
            email="test2@example.com",
            password_hash="test-password-hash",
        )

        db.session.add_all([user1, user2])
        db.session.flush()

        document1 = Document(
            user_id=user1.id,
            title="Machine Learning",
            original_filename="machine_learning.pdf",
            stored_filename="machine_learning_1.pdf",
            file_path="test_uploads/machine_learning_1.pdf",
            file_size=1000,
            page_count=2,
            processing_status="completed",
        )

        document2 = Document(
            user_id=user2.id,
            title="Artificial Intelligence",
            original_filename="artificial_intelligence.pdf",
            stored_filename="artificial_intelligence_2.pdf",
            file_path="test_uploads/artificial_intelligence_2.pdf",
            file_size=1200,
            page_count=2,
            processing_status="completed",
        )

        db.session.add_all([document1, document2])
        db.session.flush()

        chunk1 = DocumentChunk(
            user_id=user1.id,
            document_id=document1.id,
            chunk_index=0,
            page_number=1,
            content="Machine learning enables computers to learn from data.",
            token_count=10,
        )

        chunk2 = DocumentChunk(
            user_id=user1.id,
            document_id=document1.id,
            chunk_index=1,
            page_number=2,
            content="Neural networks are used in deep learning.",
            token_count=9,
        )

        chunk3 = DocumentChunk(
            user_id=user2.id,
            document_id=document2.id,
            chunk_index=0,
            page_number=1,
            content="Artificial intelligence enables intelligent machines.",
            token_count=8,
        )

        db.session.add_all([chunk1, chunk2, chunk3])
        db.session.commit()

        return {
            "user1_id": user1.id,
            "user2_id": user2.id,
            "document1_id": document1.id,
            "document2_id": document2.id,
            "chunk1_id": chunk1.id,
            "chunk2_id": chunk2.id,
            "chunk3_id": chunk3.id,
        }


@pytest.fixture
def vector_service(app):
    with app.app_context():
        service = VectorStoreService()

        # Avoid real Ollama calls during these tests.
        service.embedding_service.embeddings = MagicMock()

        service.vector_store = MagicMock()

        return service


# --------------------------------------------------
# TEST 1: Successful document indexing
# --------------------------------------------------

def test_index_document_success(
    app,
    setup_data,
    vector_service,
):
    with app.app_context():
        ids = setup_data

        vector_service.vector_store.get.return_value = {
            "ids": [],
        }

        result = vector_service.index_document(
            ids["document1_id"],
            ids["user1_id"],
        )

        assert result["indexed_chunks"] == 2
        assert result["removed_vectors"] == 0

        vector_service.vector_store.add_texts.assert_called_once()

        call_args = (
            vector_service.vector_store.add_texts.call_args
        )

        assert len(call_args.kwargs["texts"]) == 2
        assert len(call_args.kwargs["ids"]) == 2


# --------------------------------------------------
# TEST 2: Embedding IDs saved in database
# --------------------------------------------------

def test_index_document_saves_embedding_ids(
    app,
    setup_data,
    vector_service,
):
    with app.app_context():
        ids = setup_data

        vector_service.vector_store.get.return_value = {
            "ids": [],
        }

        vector_service.index_document(
            ids["document1_id"],
            ids["user1_id"],
        )

        chunks = (
            DocumentChunk.query
            .filter_by(
                document_id=ids["document1_id"],
                user_id=ids["user1_id"],
            )
            .order_by(DocumentChunk.chunk_index)
            .all()
        )

        assert len(chunks) == 2

        assert chunks[0].embedding_id == (
            f"document_{ids['document1_id']}_chunk_0"
        )

        assert chunks[1].embedding_id == (
            f"document_{ids['document1_id']}_chunk_1"
        )


# --------------------------------------------------
# TEST 3: Document not found or owned by another user
# --------------------------------------------------

def test_index_document_rejects_foreign_document(
    app,
    setup_data,
    vector_service,
):
    with app.app_context():
        ids = setup_data

        with pytest.raises(VectorStoreError):
            vector_service.index_document(
                ids["document2_id"],
                ids["user1_id"],
            )


# --------------------------------------------------
# TEST 4: Search returns matching results
# --------------------------------------------------

def test_search_returns_results(
    app,
    setup_data,
    vector_service,
):
    with app.app_context():
        ids = setup_data

        from langchain_core.documents import Document as LCDocument

        vector_service.vector_store.similarity_search_with_score.return_value = [
            (
                LCDocument(
                    page_content="Machine learning enables computers to learn.",
                    metadata={
                        "user_id": ids["user1_id"],
                        "document_id": ids["document1_id"],
                    },
                ),
                0.15,
            )
        ]

        results = vector_service.search(
            query="What is machine learning?",
            user_id=ids["user1_id"],
            top_k=5,
        )

        assert len(results) == 1

        assert "Machine learning" in results[0]["content"]

        assert results[0]["distance"] == 0.15

        call_kwargs = (
            vector_service.vector_store
            .similarity_search_with_score.call_args.kwargs
        )

        assert call_kwargs["filter"] == {
            "user_id": ids["user1_id"]
        }


# --------------------------------------------------
# TEST 5: Reject search with empty query
# --------------------------------------------------

def test_search_rejects_empty_query(
    app,
    vector_service,
):
    with app.app_context():
        with pytest.raises(VectorStoreError):
            vector_service.search(
                query="   ",
                user_id=1,
            )


# --------------------------------------------------
# TEST 6: Reject invalid top_k
# --------------------------------------------------

def test_search_rejects_invalid_top_k(
    app,
    vector_service,
):
    with app.app_context():
        with pytest.raises(VectorStoreError):
            vector_service.search(
                query="Test query",
                user_id=1,
                top_k=0,
            )


# --------------------------------------------------
# TEST 7: Reject foreign document IDs in search
# --------------------------------------------------

def test_search_rejects_foreign_document(
    app,
    setup_data,
    vector_service,
):
    with app.app_context():
        ids = setup_data

        with pytest.raises(VectorStoreError):
            vector_service.search(
                query="Artificial intelligence",
                user_id=ids["user1_id"],
                document_ids=[ids["document2_id"]],
            )


# --------------------------------------------------
# TEST 8: Re-indexing removes obsolete vectors
# --------------------------------------------------

def test_reindex_removes_obsolete_vectors(
    app,
    setup_data,
    vector_service,
):
    with app.app_context():
        ids = setup_data

        obsolete_id = (
            f"document_{ids['document1_id']}_chunk_99"
        )

        vector_service.vector_store.get.return_value = {
            "ids": [
                obsolete_id,
            ],
        }

        result = vector_service.index_document(
            ids["document1_id"],
            ids["user1_id"],
        )

        assert result["indexed_chunks"] == 2
        assert result["removed_vectors"] == 1

        vector_service.vector_store.delete.assert_called_once_with(
            ids=[obsolete_id]
        )


# --------------------------------------------------
# TEST 9: Delete document vectors
# --------------------------------------------------

def test_delete_document_vectors(
    app,
    setup_data,
    vector_service,
):
    with app.app_context():
        ids = setup_data

        vector_service.vector_store.get.return_value = {
            "ids": [
                f"document_{ids['document1_id']}_chunk_0",
                f"document_{ids['document1_id']}_chunk_1",
            ],
        }

        deleted_count = (
            vector_service.delete_document_vectors(
                ids["document1_id"],
                ids["user1_id"],
            )
        )

        assert deleted_count == 2

        vector_service.vector_store.delete.assert_called_once()


# --------------------------------------------------
# TEST 10: Reject deletion of foreign document vectors
# --------------------------------------------------

def test_delete_foreign_document_vectors(
    app,
    setup_data,
    vector_service,
):
    with app.app_context():
        ids = setup_data

        with pytest.raises(VectorStoreError):
            vector_service.delete_document_vectors(
                ids["document2_id"],
                ids["user1_id"],
            )

