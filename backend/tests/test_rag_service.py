
import pytest
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from app import create_app

from app.services.rag_service import (
    RAGService,
    RAGServiceError,
)

from app.services.retrieval_service import (
    RetrievalServiceError,
)


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def retrieval_service():
    return MagicMock()


@pytest.fixture
def llm():
    return MagicMock()


@pytest.fixture
def rag_service(app, retrieval_service, llm):
    with app.app_context():
        return RAGService(
            retrieval_service=retrieval_service,
            llm=llm,
        )


@pytest.fixture
def sample_retrieval_result():
    return {
        "query": "What is machine learning?",
        "result_count": 2,
        "passages": [
            {
                "source_number": 1,
                "content": (
                    "Machine learning allows computers "
                    "to learn from data."
                ),
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
            },
            {
                "source_number": 2,
                "content": (
                    "Neural networks are used in deep learning."
                ),
                "document": {
                    "id": 10,
                    "title": "Machine Learning Research",
                    "filename": "ml.pdf",
                },
                "citation": {
                    "document_id": 10,
                    "document_title": "Machine Learning Research",
                    "page_number": 4,
                    "chunk_id": 26,
                },
            },
        ],
        "context": (
            "[Source 1]\n"
            "Document: Machine Learning Research\n"
            "Page: 3\n"
            "Machine learning allows computers to learn from data."
        ),
        "sources": [
            {
                "document_id": 10,
                "document_title": "Machine Learning Research",
                "page_number": 3,
                "chunk_id": 25,
            },
            {
                "document_id": 10,
                "document_title": "Machine Learning Research",
                "page_number": 4,
                "chunk_id": 26,
            },
        ],
    }


# --------------------------------------------------
# TEST 1: Successful RAG answer generation
# --------------------------------------------------

def test_generate_answer_success(
    rag_service,
    retrieval_service,
    llm,
    sample_retrieval_result,
):
    retrieval_service.retrieve_with_context.return_value = (
        sample_retrieval_result
    )

    llm.invoke.return_value = AIMessage(
        content=(
            "Machine learning enables computers "
            "to learn patterns from data. "
            "[Source 1, Page 3]"
        )
    )

    result = rag_service.generate_answer(
        question="What is machine learning?",
        user_id=1,
    )

    assert "Machine learning" in result["answer"]
    assert result["model"] == "llama3.2:3b"
    assert result["retrieved_count"] == 2
    assert result["grounded"] is True
    assert len(result["sources"]) == 2

    retrieval_service.retrieve_with_context.assert_called_once()
    llm.invoke.assert_called_once()


# --------------------------------------------------
# TEST 2: Verify retrieval arguments
# --------------------------------------------------

def test_generate_answer_passes_retrieval_arguments(
    rag_service,
    retrieval_service,
    llm,
    sample_retrieval_result,
):
    retrieval_service.retrieve_with_context.return_value = (
        sample_retrieval_result
    )

    llm.invoke.return_value = AIMessage(
        content="Test answer."
    )

    rag_service.generate_answer(
        question="Explain neural networks",
        user_id=5,
        document_ids=[10, 11],
        top_k=7,
    )

    retrieval_service.retrieve_with_context.assert_called_once_with(
        query="Explain neural networks",
        user_id=5,
        document_ids=[10, 11],
        top_k=7,
    )


# --------------------------------------------------
# TEST 3: Return fallback when no passages are found
# --------------------------------------------------

def test_generate_answer_without_relevant_passages(
    rag_service,
    retrieval_service,
    llm,
):
    retrieval_service.retrieve_with_context.return_value = {
        "query": "Unknown question",
        "result_count": 0,
        "passages": [],
        "context": "",
        "sources": [],
    }

    result = rag_service.generate_answer(
        question="Unknown question",
        user_id=1,
    )

    assert result["grounded"] is False
    assert result["retrieved_count"] == 0
    assert result["sources"] == []
    assert "couldn't find relevant information" in (
        result["answer"]
    ).lower()

    # LLM must not be called without retrieved evidence.
    llm.invoke.assert_not_called()


# --------------------------------------------------
# TEST 4: Reject empty question
# --------------------------------------------------

@pytest.mark.parametrize(
    "question",
    ["", "   ", None],
)
def test_generate_answer_rejects_empty_question(
    rag_service,
    question,
):
    with pytest.raises(RAGServiceError):
        rag_service.generate_answer(
            question=question,
            user_id=1,
        )


# --------------------------------------------------
# TEST 5: Reject invalid top_k
# --------------------------------------------------

@pytest.mark.parametrize(
    "top_k",
    [0, -1, 21, True, "5"],
)
def test_generate_answer_rejects_invalid_top_k(
    rag_service,
    top_k,
):
    with pytest.raises(RAGServiceError):
        rag_service.generate_answer(
            question="Explain artificial intelligence",
            user_id=1,
            top_k=top_k,
        )


# --------------------------------------------------
# TEST 6: Verify prompt contains question and context
# --------------------------------------------------

def test_build_prompt_contains_question_and_context():
    question = "What is deep learning?"

    context = (
        "[Source 1]\n"
        "Document: AI Research\n"
        "Page: 5\n"
        "Deep learning uses neural networks."
    )

    prompt = RAGService.build_prompt(
        question=question,
        context=context,
    )

    assert question in prompt
    assert context in prompt
    assert "DOCUMENT EXCERPTS" in prompt
    assert "USER QUESTION" in prompt
    assert "Do not invent facts" in prompt


# --------------------------------------------------
# TEST 7: Handle retrieval service errors
# --------------------------------------------------

def test_generate_answer_handles_retrieval_error(
    rag_service,
    retrieval_service,
):
    retrieval_service.retrieve_with_context.side_effect = (
        RetrievalServiceError("Retrieval failed")
    )

    with pytest.raises(RAGServiceError):
        rag_service.generate_answer(
            question="Explain AI",
            user_id=1,
        )


# --------------------------------------------------
# TEST 8: Handle Ollama generation errors
# --------------------------------------------------

def test_generate_answer_handles_llm_error(
    rag_service,
    retrieval_service,
    llm,
    sample_retrieval_result,
):
    retrieval_service.retrieve_with_context.return_value = (
        sample_retrieval_result
    )

    llm.invoke.side_effect = Exception(
        "Ollama server unavailable"
    )

    with pytest.raises(RAGServiceError):
        rag_service.generate_answer(
            question="Explain AI",
            user_id=1,
        )


# --------------------------------------------------
# TEST 9: Reject empty LLM response
# --------------------------------------------------

def test_generate_answer_rejects_empty_llm_response(
    rag_service,
    retrieval_service,
    llm,
    sample_retrieval_result,
):
    retrieval_service.retrieve_with_context.return_value = (
        sample_retrieval_result
    )

    llm.invoke.return_value = AIMessage(content="   ")

    with pytest.raises(RAGServiceError):
        rag_service.generate_answer(
            question="Explain AI",
            user_id=1,
        )


# --------------------------------------------------
# TEST 10: Handle list-based LLM response content
# --------------------------------------------------

def test_generate_answer_handles_list_response(
    rag_service,
    retrieval_service,
    llm,
    sample_retrieval_result,
):
    retrieval_service.retrieve_with_context.return_value = (
        sample_retrieval_result
    )

    llm.invoke.return_value = AIMessage(
        content=[
            {"type": "text", "text": "Machine learning"},
            {"type": "text", "text": "learns from data."},
        ]
    )

    result = rag_service.generate_answer(
        question="Explain machine learning",
        user_id=1,
    )

    assert result["answer"] == (
        "Machine learning learns from data."
    )


# --------------------------------------------------
# TEST 11: Preserve source citations
# --------------------------------------------------

def test_generate_answer_preserves_sources(
    rag_service,
    retrieval_service,
    llm,
    sample_retrieval_result,
):
    retrieval_service.retrieve_with_context.return_value = (
        sample_retrieval_result
    )

    llm.invoke.return_value = AIMessage(
        content="Machine learning learns from data."
    )

    result = rag_service.generate_answer(
        question="Explain machine learning",
        user_id=1,
    )

    assert result["sources"] == (
        sample_retrieval_result["sources"]
    )

    assert result["sources"][0]["page_number"] == 3
    assert result["sources"][1]["page_number"] == 4
