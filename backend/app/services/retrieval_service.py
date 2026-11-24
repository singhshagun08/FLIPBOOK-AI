
from typing import Any, Dict, List, Optional

from app.models import Document
from app.services.vector_store_service import (
    VectorStoreService,
    VectorStoreError,
)


class RetrievalServiceError(Exception):
    """Raised when document retrieval fails."""


class RetrievalService:
    """Retrieve relevant document passages for RAG."""

    def __init__(
        self,
        vector_store_service: Optional[VectorStoreService] = None,
    ):
        self.vector_store = (
            vector_store_service or VectorStoreService()
        )

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    @staticmethod
    def validate_query(query: str) -> str:
        if not isinstance(query, str) or not query.strip():
            raise RetrievalServiceError(
                "Search query cannot be empty."
            )

        return query.strip()

    @staticmethod
    def validate_user_id(user_id: int) -> int:
        if (
            not isinstance(user_id, int)
            or isinstance(user_id, bool)
            or user_id < 1
        ):
            raise RetrievalServiceError(
                "A valid user ID is required."
            )

        return user_id

    @staticmethod
    def validate_top_k(top_k: int) -> int:
        if (
            not isinstance(top_k, int)
            or isinstance(top_k, bool)
            or top_k < 1
            or top_k > 50
        ):
            raise RetrievalServiceError(
                "top_k must be an integer between 1 and 50."
            )

        return top_k

    # --------------------------------------------------
    # DOCUMENT METADATA
    # --------------------------------------------------

    @staticmethod
    def get_document_metadata(
        document_ids: List[int],
        user_id: int,
    ) -> Dict[int, Document]:

        if not document_ids:
            return {}

        documents = (
            Document.query
            .filter(
                Document.user_id == user_id,
                Document.id.in_(document_ids),
            )
            .all()
        )

        return {
            document.id: document
            for document in documents
        }

    # --------------------------------------------------
    # SEMANTIC RETRIEVAL
    # --------------------------------------------------

    def retrieve(
        self,
        query: str,
        user_id: int,
        document_ids: Optional[List[int]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant passages from a user's documents.

        Args:
            query: Natural-language question.
            user_id: Authenticated user ID.
            document_ids: Optional selected document IDs.
            top_k: Maximum number of results.

        Returns:
            List of passages with source metadata and distances.
        """

        query = self.validate_query(query)
        user_id = self.validate_user_id(user_id)
        top_k = self.validate_top_k(top_k)

        if document_ids is not None:
            if (
                not isinstance(document_ids, list)
                or not document_ids
                or any(
                    not isinstance(doc_id, int)
                    or isinstance(doc_id, bool)
                    or doc_id < 1
                    for doc_id in document_ids
                )
            ):
                raise RetrievalServiceError(
                    "Document IDs must be a non-empty list "
                    "of positive integers."
                )

            document_ids = list(dict.fromkeys(document_ids))

        try:
            # Search ChromaDB.
            search_results = self.vector_store.search(
                query=query,
                user_id=user_id,
                document_ids=document_ids,
                top_k=top_k,
            )

            if not search_results:
                return []

            # Collect document IDs from retrieved chunks.
            retrieved_document_ids = list({
                result["metadata"].get("document_id")
                for result in search_results
                if result.get("metadata", {}).get("document_id")
                is not None
            })

            # Fetch document details while enforcing ownership.
            documents = self.get_document_metadata(
                retrieved_document_ids,
                user_id,
            )

            retrieved_passages = []

            for index, result in enumerate(
                search_results,
                start=1,
            ):
                metadata = result.get("metadata", {})

                document_id = metadata.get("document_id")

                document = documents.get(document_id)

                # Never return a passage without a verified
                # document belonging to the authenticated user.
                if document is None:
                    continue

                page_number = metadata.get("page_number")

                retrieved_passages.append({
                    "source_number": index,
                    "content": result["content"],
                    "distance": result["distance"],

                    "document": {
                        "id": document.id,
                        "title": document.title,
                        "filename": document.original_filename,
                    },

                    "chunk": {
                        "id": metadata.get("chunk_id"),
                        "index": metadata.get("chunk_index"),
                    },

                    "page_number": page_number,

                    "citation": {
                        "document_id": document.id,
                        "document_title": document.title,
                        "page_number": page_number,
                        "chunk_id": metadata.get("chunk_id"),
                    },
                })

            return retrieved_passages

        except VectorStoreError as exc:
            raise RetrievalServiceError(
                f"Document search failed: {exc}"
            ) from exc

        except RetrievalServiceError:
            raise

        except Exception as exc:
            raise RetrievalServiceError(
                f"Retrieval failed: {exc}"
            ) from exc

    # --------------------------------------------------
    # CONTEXT GENERATION
    # --------------------------------------------------

    @staticmethod
    def build_context(
        passages: List[Dict[str, Any]],
    ) -> str:
        """
        Convert retrieved passages into source-labelled
        context for the language model.
        """

        if not passages:
            return ""

        context_parts = []

        for passage in passages:
            document = passage["document"]
            citation = passage["citation"]

            source_number = passage["source_number"]
            page_number = citation["page_number"]

            page_reference = (
                str(page_number)
                if page_number is not None
                else "Unknown"
            )

            source_header = (
                f"[Source {source_number}]\n"
                f"Document: {document['title']}\n"
                f"Document ID: {document['id']}\n"
                f"Page: {page_reference}\n"
                f"Chunk ID: {citation['chunk_id']}"
            )

            context_parts.append(
                f"{source_header}\n"
                f"Content:\n{passage['content']}"
            )

        return "\n\n---\n\n".join(context_parts)

    # --------------------------------------------------
    # COMPLETE RETRIEVAL RESPONSE
    # --------------------------------------------------

    def retrieve_with_context(
        self,
        query: str,
        user_id: int,
        document_ids: Optional[List[int]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Retrieve passages and generate formatted LLM context.
        """

        passages = self.retrieve(
            query=query,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k,
        )

        context = self.build_context(passages)

        return {
            "query": query.strip(),
            "result_count": len(passages),
            "passages": passages,
            "context": context,
            "sources": [
                passage["citation"]
                for passage in passages
            ],
        }


# --------------------------------------------------
# SERVICE FACTORY
# --------------------------------------------------

def get_retrieval_service() -> RetrievalService:
    """Create and return a retrieval service."""

    return RetrievalService()
