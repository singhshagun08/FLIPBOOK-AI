
from typing import List, Optional

from flask import current_app
from langchain_ollama import OllamaEmbeddings


class EmbeddingServiceError(Exception):
    """Raised when text embedding generation fails."""


class EmbeddingService:
    """Generate text embeddings using Ollama."""

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model or current_app.config.get(
            "OLLAMA_EMBEDDING_MODEL",
            "nomic-embed-text",
        )

        self.base_url = base_url or current_app.config.get(
            "OLLAMA_BASE_URL",
            "http://localhost:11434",
        )

        try:
            self.embeddings = OllamaEmbeddings(
                model=self.model,
                base_url=self.base_url,
            )
        except Exception as exc:
            raise EmbeddingServiceError(
                f"Could not initialize Ollama embeddings: {exc}"
            ) from exc

    def embed_query(self, text: str) -> List[float]:
        """Generate an embedding for a single search query."""

        if not isinstance(text, str) or not text.strip():
            raise EmbeddingServiceError(
                "Query text cannot be empty."
            )

        try:
            vector = self.embeddings.embed_query(text.strip())

            if not vector:
                raise EmbeddingServiceError(
                    "Ollama returned an empty embedding."
                )

            return vector

        except EmbeddingServiceError:
            raise
        except Exception as exc:
            raise EmbeddingServiceError(
                f"Query embedding generation failed: {exc}"
            ) from exc

    def embed_documents(
        self,
        texts: List[str],
        batch_size: int = 32,
    ) -> List[List[float]]:
        """Generate embeddings for multiple document chunks."""

        if not isinstance(texts, list) or not texts:
            raise EmbeddingServiceError(
                "Document text list cannot be empty."
            )

        if (
            not isinstance(batch_size, int)
            or isinstance(batch_size, bool)
            or batch_size < 1
        ):
            raise EmbeddingServiceError(
                "Batch size must be a positive integer."
            )

        if any(
            not isinstance(text, str) or not text.strip()
            for text in texts
        ):
            raise EmbeddingServiceError(
                "Document chunks cannot contain empty text."
            )

        all_vectors = []

        try:
            for start in range(0, len(texts), batch_size):
                batch = texts[start:start + batch_size]

                vectors = self.embeddings.embed_documents(
                    [text.strip() for text in batch]
                )

                if len(vectors) != len(batch):
                    raise EmbeddingServiceError(
                        "Embedding count does not match chunk count."
                    )

                all_vectors.extend(vectors)

            return all_vectors

        except EmbeddingServiceError:
            raise
        except Exception as exc:
            raise EmbeddingServiceError(
                f"Document embedding generation failed: {exc}"
            ) from exc


def get_embedding_service() -> EmbeddingService:
    """Return an initialized embedding service."""

    return EmbeddingService()
