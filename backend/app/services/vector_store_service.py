
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import current_app
from langchain_chroma import Chroma

from app.extensions import db
from app.models import Document, DocumentChunk
from app.services.embedding_service import (
    EmbeddingService,
    EmbeddingServiceError,
)


class VectorStoreError(Exception):
    """Raised when vector storage operations fail."""


class VectorStoreService:
    """Manage persistent document vectors using ChromaDB."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.embedding_service = (
            embedding_service or EmbeddingService()
        )

        self.persist_directory = Path(
            current_app.config["CHROMA_PERSIST_DIRECTORY"]
        )

        self.collection_name = current_app.config.get(
            "CHROMA_COLLECTION_NAME",
            "flipbook_documents",
        )

        self.persist_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_service.embeddings,
                persist_directory=str(self.persist_directory),
            )

        except Exception as exc:
            raise VectorStoreError(
                f"Could not initialize ChromaDB: {exc}"
            ) from exc

    # ========================================================
    # VECTOR ID AND METADATA HELPERS
    # ========================================================

    @staticmethod
    def _get_vector_id(
        document_id: int,
        chunk_index: int,
    ) -> str:
        """Generate a stable ID for a document chunk."""

        return f"document_{document_id}_chunk_{chunk_index}"

    @staticmethod
    def _build_metadata(
        chunk: DocumentChunk,
    ) -> Dict[str, Any]:
        """Build Chroma-compatible scalar metadata."""

        metadata = {
            "user_id": int(chunk.user_id),
            "document_id": int(chunk.document_id),
            "chunk_id": int(chunk.id),
            "chunk_index": int(chunk.chunk_index),
        }

        if chunk.page_number is not None:
            metadata["page_number"] = int(chunk.page_number)

        if chunk.token_count is not None:
            metadata["token_count"] = int(chunk.token_count)

        return metadata

    @staticmethod
    def _build_document_filter(
        user_id: int,
        document_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Build a valid ChromaDB metadata filter.

        No document IDs:
            Filter by user ID.

        One document ID:
            Filter by user ID AND document ID.

        Multiple document IDs:
            Filter by user ID AND an OR condition
            containing all selected document IDs.
        """

        user_id = int(user_id)

        if not document_ids:
            return {
                "user_id": user_id
            }

        normalized_ids = [
            int(document_id)
            for document_id in document_ids
        ]

        if len(normalized_ids) == 1:
            return {
                "$and": [
                    {"user_id": user_id},
                    {"document_id": normalized_ids[0]},
                ]
            }

        return {
            "$and": [
                {"user_id": user_id},
                {
                    "$or": [
                        {"document_id": document_id}
                        for document_id in normalized_ids
                    ]
                },
            ]
        }

    # ========================================================
    # INDEX DOCUMENT
    # ========================================================

    def index_document(
        self,
        document_id: int,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Index all stored chunks belonging to a user's document.

        Existing vectors are updated using stable IDs.
        Obsolete vectors are removed after successful insertion.
        """

        document = Document.query.filter_by(
            id=document_id,
            user_id=user_id,
        ).first()

        if document is None:
            raise VectorStoreError(
                "Document not found or access denied."
            )

        chunks = (
            DocumentChunk.query
            .filter_by(
                document_id=document_id,
                user_id=user_id,
            )
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )

        if not chunks:
            raise VectorStoreError(
                "No processed document chunks are available."
            )

        texts = [
            chunk.content
            for chunk in chunks
        ]

        if any(
            not text or not text.strip()
            for text in texts
        ):
            raise VectorStoreError(
                "One or more document chunks contain empty text."
            )

        vector_ids = [
            self._get_vector_id(
                document_id,
                chunk.chunk_index,
            )
            for chunk in chunks
        ]

        metadatas = [
            self._build_metadata(chunk)
            for chunk in chunks
        ]

        try:
            # Insert or update vectors using stable IDs.
            self.vector_store.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=vector_ids,
            )

            # Find existing vectors belonging to this document.
            existing = self.vector_store.get(
                where=self._build_document_filter(
                    user_id=user_id,
                    document_ids=[document_id],
                ),
                include=[],
            )

            existing_ids = set(
                existing.get("ids", [])
            )

            current_ids = set(vector_ids)

            stale_ids = list(
                existing_ids - current_ids
            )

            # Remove obsolete vectors.
            if stale_ids:
                self.vector_store.delete(
                    ids=stale_ids
                )

            # Save vector IDs in relational database.
            for chunk, vector_id in zip(
                chunks,
                vector_ids,
            ):
                chunk.embedding_id = vector_id

            db.session.commit()

            return {
                "document_id": document_id,
                "user_id": user_id,
                "indexed_chunks": len(chunks),
                "removed_vectors": len(stale_ids),
                "collection": self.collection_name,
            }

        except Exception as exc:
            db.session.rollback()

            raise VectorStoreError(
                f"Document indexing failed: {exc}"
            ) from exc

    # ========================================================
    # SEMANTIC SEARCH
    # ========================================================

    def search(
        self,
        query: str,
        user_id: int,
        document_ids: Optional[List[int]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search vectors while enforcing user-level isolation.

        Optionally restrict results to selected document IDs.
        """

        if not isinstance(query, str) or not query.strip():
            raise VectorStoreError(
                "Search query cannot be empty."
            )

        if (
            not isinstance(top_k, int)
            or isinstance(top_k, bool)
            or top_k < 1
        ):
            raise VectorStoreError(
                "top_k must be a positive integer."
            )

        if (
            not isinstance(user_id, int)
            or isinstance(user_id, bool)
            or user_id < 1
        ):
            raise VectorStoreError(
                "user_id must be a positive integer."
            )

        # Validate selected document IDs and ownership.
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
                raise VectorStoreError(
                    "Document IDs must be a non-empty list "
                    "of positive integers."
                )

            # Remove duplicate IDs without changing their order.
            document_ids = list(
                dict.fromkeys(document_ids)
            )

            owned_documents = (
                Document.query
                .filter(
                    Document.user_id == user_id,
                    Document.id.in_(document_ids),
                )
                .all()
            )

            owned_ids = {
                document.id
                for document in owned_documents
            }

            if owned_ids != set(document_ids):
                raise VectorStoreError(
                    "One or more documents do not belong "
                    "to this user."
                )

        # Build a ChromaDB-compatible filter.
        where_filter = self._build_document_filter(
            user_id=user_id,
            document_ids=document_ids,
        )

        try:
            results = (
                self.vector_store.similarity_search_with_score(
                    query=query.strip(),
                    k=top_k,
                    filter=where_filter,
                )
            )

            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "distance": float(score),
                }
                for doc, score in results
            ]

        except Exception as exc:
            raise VectorStoreError(
                f"Vector search failed: {exc}"
            ) from exc

    # ========================================================
    # DELETE DOCUMENT VECTORS
    # ========================================================

    def delete_document_vectors(
        self,
        document_id: int,
        user_id: int,
    ) -> int:
        """
        Delete vectors belonging to a specific user's document.

        Also clears relational references to deleted vectors.
        """

        document = Document.query.filter_by(
            id=document_id,
            user_id=user_id,
        ).first()

        if document is None:
            raise VectorStoreError(
                "Document not found or access denied."
            )

        try:
            existing = self.vector_store.get(
                where=self._build_document_filter(
                    user_id=user_id,
                    document_ids=[document_id],
                ),
                include=[],
            )

            vector_ids = existing.get("ids", [])

            if vector_ids:
                self.vector_store.delete(
                    ids=vector_ids
                )

            # Clear database references.
            DocumentChunk.query.filter_by(
                document_id=document_id,
                user_id=user_id,
            ).update(
                {
                    DocumentChunk.embedding_id: None
                },
                synchronize_session="fetch",
            )

            db.session.commit()

            return len(vector_ids)

        except Exception as exc:
            db.session.rollback()

            raise VectorStoreError(
                f"Vector deletion failed: {exc}"
            ) from exc


# ============================================================
# SERVICE FACTORY
# ============================================================

def get_vector_store_service() -> VectorStoreService:
    """Create and return the vector store service."""

    return VectorStoreService()
