
import pytest
from unittest.mock import MagicMock

from app import create_app
from app.services.embedding_service import (
    EmbeddingService,
    EmbeddingServiceError,
)


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def service(app):
    with app.app_context():
        instance = EmbeddingService()
        instance.embeddings = MagicMock()
        return instance


# --------------------------------------------------
# TEST 1: Successful query embedding
# --------------------------------------------------

def test_embed_query_success(service):
    service.embeddings.embed_query.return_value = [
        0.1,
        0.2,
        0.3,
    ]

    result = service.embed_query(
        "What is machine learning?"
    )

    assert result == [0.1, 0.2, 0.3]

    service.embeddings.embed_query.assert_called_once_with(
        "What is machine learning?"
    )


# --------------------------------------------------
# TEST 2: Reject empty query
# --------------------------------------------------

def test_embed_query_rejects_empty_text(service):
    with pytest.raises(EmbeddingServiceError):
        service.embed_query("   ")


# --------------------------------------------------
# TEST 3: Handle Ollama query errors
# --------------------------------------------------

def test_embed_query_handles_ollama_error(service):
    service.embeddings.embed_query.side_effect = Exception(
        "Ollama unavailable"
    )

    with pytest.raises(EmbeddingServiceError):
        service.embed_query("Explain artificial intelligence")


# --------------------------------------------------
# TEST 4: Successful document embedding with batching
# --------------------------------------------------

def test_embed_documents_success(service):
    # First call receives 2 chunks.
    # Second call receives the remaining 1 chunk.

    service.embeddings.embed_documents.side_effect = [
        [
            [0.1, 0.2],
            [0.3, 0.4],
        ],
        [
            [0.5, 0.6],
        ],
    ]

    result = service.embed_documents(
        [
            "First chunk",
            "Second chunk",
            "Third chunk",
        ],
        batch_size=2,
    )

    assert len(result) == 3

    assert result == [
        [0.1, 0.2],
        [0.3, 0.4],
        [0.5, 0.6],
    ]

    assert service.embeddings.embed_documents.call_count == 2


# --------------------------------------------------
# TEST 5: Reject empty document list
# --------------------------------------------------

def test_embed_documents_rejects_empty_list(service):
    with pytest.raises(EmbeddingServiceError):
        service.embed_documents([])


# --------------------------------------------------
# TEST 6: Reject empty document chunks
# --------------------------------------------------

def test_embed_documents_rejects_empty_chunk(service):
    with pytest.raises(EmbeddingServiceError):
        service.embed_documents(
            [
                "Valid text",
                "   ",
            ]
        )


# --------------------------------------------------
# TEST 7: Reject invalid batch size
# --------------------------------------------------

def test_embed_documents_rejects_invalid_batch_size(service):
    with pytest.raises(EmbeddingServiceError):
        service.embed_documents(
            ["Valid text"],
            batch_size=0,
        )


# --------------------------------------------------
# TEST 8: Handle Ollama document embedding errors
# --------------------------------------------------

def test_embed_documents_handles_ollama_error(service):
    service.embeddings.embed_documents.side_effect = Exception(
        "Ollama unavailable"
    )

    with pytest.raises(EmbeddingServiceError):
        service.embed_documents(
            ["Test document chunk"]
        )
