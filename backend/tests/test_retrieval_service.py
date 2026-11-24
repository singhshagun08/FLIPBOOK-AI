
import pytest
from unittest.mock import MagicMock

from app import create_app
from app.extensions import db
from app.models import User, Document

from app.services.retrieval_service import (
    RetrievalService,
    RetrievalServiceError,
)

from app.services.vector_store_service import VectorStoreError


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
            username="retrieval_user1",
            email="retrieval1@example.com",
            password_hash="test-password-hash",
        )

        user2 = User(
            full_name="Test User Two",
            username="retrieval_user2",
            email="retrieval2@example.com",
            password_hash="test-password-hash",
        )

        db.session.add_all([user1, user2])
        db.session.flush()

        document1 = Document(
            user_id=user1.id,
            title="Machine Learning Research",
            original_filename="machine_learning.pdf",
            stored_filename="machine_learning_test.pdf",
            file_path="temporary/machine_learning.pdf",
            file_size=1000,
            page_count=5,
            processing_status="completed",
        )

        document2 = Document(
            user_id=user2.id,
            title="Artificial Intelligence Research",
            original_filename="ai_research.pdf",
            stored_filename="ai_research_test.pdf",
            file_path="temporary/ai_research.pdf",
            file_size=1200,
            page_count=8,
            processing_status="completed",
        )

        db.session.add_all([document1, document2])
        db.session.commit()

        return {
            "user1_id": user1.id,
            "user2_id": user2.id,
            "document1_id": document1.id,
            "document2_id": document2.id,
        }


@pytest.fixture
def retrieval_service(app):
    with app.app_context():
        mock_vector_store = MagicMock()

        service = RetrievalService(
            vector_store_service=mock_vector_store
        )

        return service


def make_search_result(
    document_id,
    chunk_id=1,
    chunk_index=0,
    page_number=1,
    content="Machine learning enables computers to learn.",
    user_id=1,
):
    return {
        "content": content,
        "distance": 0.25,
        "metadata": {
            "user_id": user_id,
            "document_id": document_id,
            "chunk_id": chunk_id,
            "chunk_index": chunk_index,
            "page_number": page_number,
        },
    }


# --------------------------------------------------
# TEST 1: Successful retrieval
# --------------------------------------------------

def test_retrieve_success(
    app,
    setup_data,
    retrieval_service,
):
    with app.app_context():
        ids = setup_data

        retrieval_service.vector_store.search.return_value = [
            make_search_result(
                document_id=ids["document1_id"],
                user_id=ids["user1_id"],
            )
        ]

        results = retrieval_service.retrieve(
            query="Explain machine learning",
            user_id=ids["user1_id"],
        )

        assert len(results) == 1

        assert results[0]["content"].startswith(
            "Machine learning"
        )

        assert results[0]["document"]["title"] == (
            "Machine Learning Research"
        )

        assert results[0]["page_number"] == 1


# --------------------------------------------------
# TEST 2: Preserve citation metadata
# --------------------------------------------------

def test_retrieve_preserves_citations(
    app,
    setup_data,
    retrieval_service,
):
    with app.app_context():
        ids = setup_data

        retrieval_service.vector_store.search.return_value = [
            make_search_result(
                document_id=ids["document1_id"],
                chunk_id=15,
                chunk_index=3,
                page_number=4,
                user_id=ids["user1_id"],
            )
        ]

        results = retrieval_service.retrieve(
            query="Explain neural networks",
            user_id=ids["user1_id"],
        )

        citation = results[0]["citation"]

        assert citation["document_id"] == ids["document1_id"]
        assert citation["page_number"] == 4
        assert citation["chunk_id"] == 15


# --------------------------------------------------
# TEST 3: Empty search results
# --------------------------------------------------

def test_retrieve_returns_empty_list(
    app,
    retrieval_service,
):
    with app.app_context():
        retrieval_service.vector_store.search.return_value = []

        results = retrieval_service.retrieve(
            query="Unknown topic",
            user_id=1,
        )

        assert results == []


# --------------------------------------------------
# TEST 4: Reject empty query
# --------------------------------------------------

def test_retrieve_rejects_empty_query(
    app,
    retrieval_service,
):
    with app.app_context():
        with pytest.raises(RetrievalServiceError):
            retrieval_service.retrieve(
                query="   ",
                user_id=1,
            )


# --------------------------------------------------
# TEST 5: Reject invalid user ID
# --------------------------------------------------

@pytest.mark.parametrize(
    "user_id",
    [0, -1, "abc", None, True],
)
def test_retrieve_rejects_invalid_user_id(
    app,
    retrieval_service,
    user_id,
):
    with app.app_context():
        with pytest.raises(RetrievalServiceError):
            retrieval_service.retrieve(
                query="Test query",
                user_id=user_id,
            )


# --------------------------------------------------
# TEST 6: Reject invalid top_k
# --------------------------------------------------

@pytest.mark.parametrize(
    "top_k",
    [0, -1, 51, True, "5"],
)
def test_retrieve_rejects_invalid_top_k(
    app,
    retrieval_service,
    top_k,
):
    with app.app_context():
        with pytest.raises(RetrievalServiceError):
            retrieval_service.retrieve(
                query="Test query",
                user_id=1,
                top_k=top_k,
            )


# --------------------------------------------------
# TEST 7: Reject empty document ID list
# --------------------------------------------------

def test_retrieve_rejects_empty_document_ids(
    app,
    retrieval_service,
):
    with app.app_context():
        with pytest.raises(RetrievalServiceError):
            retrieval_service.retrieve(
                query="Test query",
                user_id=1,
                document_ids=[],
            )


# --------------------------------------------------
# TEST 8: Reject foreign document references
# --------------------------------------------------

def test_retrieve_rejects_foreign_document_results(
    app,
    setup_data,
    retrieval_service,
):
    with app.app_context():
        ids = setup_data

        retrieval_service.vector_store.search.return_value = [
            make_search_result(
                document_id=ids["document2_id"],
                user_id=ids["user2_id"],
            )
        ]

        results = retrieval_service.retrieve(
            query="Artificial intelligence",
            user_id=ids["user1_id"],
        )

        # The document does not belong to user 1.
        assert results == []


# --------------------------------------------------
# TEST 9: Convert passages into LLM context
# --------------------------------------------------

def test_build_context():
    passages = [
        {
            "source_number": 1,
            "content": "Machine learning learns from data.",
            "document": {
                "id": 10,
                "title": "Machine Learning Research",
                "filename": "ml.pdf",
            },
            "citation": {
                "document_id": 10,
                "document_title": "Machine Learning Research",
                "page_number": 3,
                "chunk_id": 25,
            },
        }
    ]

    context = RetrievalService.build_context(passages)

    assert "[Source 1]" in context
    assert "Machine Learning Research" in context
    assert "Page: 3" in context
    assert "Chunk ID: 25" in context
    assert "Machine learning learns from data." in context


# --------------------------------------------------
# TEST 10: Empty context
# --------------------------------------------------

def test_build_empty_context():
    context = RetrievalService.build_context([])

    assert context == ""


# --------------------------------------------------
# TEST 11: Complete retrieval with context
# --------------------------------------------------

def test_retrieve_with_context(
    app,
    setup_data,
    retrieval_service,
):
    with app.app_context():
        ids = setup_data

        retrieval_service.vector_store.search.return_value = [
            make_search_result(
                document_id=ids["document1_id"],
                user_id=ids["user1_id"],
            )
        ]

        result = retrieval_service.retrieve_with_context(
            query="What is machine learning?",
            user_id=ids["user1_id"],
            top_k=5,
        )

        assert result["result_count"] == 1
        assert len(result["passages"]) == 1
        assert len(result["sources"]) == 1

        assert "Machine learning" in result["context"]

        assert result["query"] == (
            "What is machine learning?"
        )


# --------------------------------------------------
# TEST 12: Handle vector store errors
# --------------------------------------------------

def test_retrieve_handles_vector_store_error(
    app,
    retrieval_service,
):
    with app.app_context():
        retrieval_service.vector_store.search.side_effect = (
            VectorStoreError("ChromaDB unavailable")
        )

        with pytest.raises(RetrievalServiceError):
            retrieval_service.retrieve(
                query="Test query",
                user_id=1,
            )


# --------------------------------------------------
# TEST 13: Remove duplicate selected document IDs
# --------------------------------------------------

def test_retrieve_removes_duplicate_document_ids(
    app,
    setup_data,
    retrieval_service,
):
    with app.app_context():
        ids = setup_data

        retrieval_service.vector_store.search.return_value = []

        retrieval_service.retrieve(
            query="Machine learning",
            user_id=ids["user1_id"],
            document_ids=[
                ids["document1_id"],
                ids["document1_id"],
            ],
        )

        call_kwargs = (
            retrieval_service.vector_store.search.call_args.kwargs
        )

        assert call_kwargs["document_ids"] == [
            ids["document1_id"]
        ]
