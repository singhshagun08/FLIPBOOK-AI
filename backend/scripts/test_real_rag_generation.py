import sys
from pathlib import Path

# Add the backend directory to Python's import path.
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app
from app.services.rag_service import RAGService


class MockRetrievalService:
    """Provides sample document context without accessing the database."""

    def retrieve_with_context(
        self,
        query,
        user_id,
        document_ids=None,
        top_k=5,
    ):
        return {
            "query": query,
            "result_count": 1,
            "context": """
            Source 1:
            Document: Introduction to Machine Learning
            Page: 2

            Machine learning is a branch of artificial intelligence.
            It enables computer systems to learn patterns from data
            and improve their performance without being explicitly
            programmed for every task.
            """,
            "passages": [
                {
                    "source_number": 1,
                    "content": (
                        "Machine learning enables computer systems "
                        "to learn patterns from data."
                    ),
                    "page_number": 2,
                    "citation": {
                        "document_id": 1,
                        "document_title": "Introduction to Machine Learning",
                        "page_number": 2,
                        "chunk_id": 1,
                    },
                }
            ],
            "sources": [
                {
                    "document_id": 1,
                    "document_title": "Introduction to Machine Learning",
                    "page_number": 2,
                    "chunk_id": 1,
                }
            ],
        }


def main():
    app = create_app()

    with app.app_context():
        retrieval_service = MockRetrievalService()

        rag_service = RAGService(
            retrieval_service=retrieval_service
        )

        question = (
            "What is machine learning, according to the document? "
            "Answer briefly and cite the source."
        )

        print("\nTesting real Ollama RAG generation...")
        print(f"Model: {app.config['OLLAMA_CHAT_MODEL']}")
        print(f"Question: {question}\n")

        result = rag_service.generate_answer(
            question=question,
            user_id=1,
            top_k=3,
        )

        print("=" * 60)
        print("GENERATED ANSWER")
        print("=" * 60)
        print(result["answer"])

        print("\n" + "=" * 60)
        print("RESULT DETAILS")
        print("=" * 60)
        print(f"Model: {result['model']}")
        print(f"Grounded: {result['grounded']}")
        print(f"Retrieved passages: {result['retrieved_count']}")
        print(f"Sources: {result['sources']}")

        if not result["answer"].strip():
            raise RuntimeError("The model returned an empty answer.")

        print("\nREAL OLLAMA RAG GENERATION SUCCESSFUL")


if __name__ == "__main__":
    main()