
from datetime import datetime, timezone

from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    Index,
    UniqueConstraint,
    CheckConstraint
)
from sqlalchemy.types import JSON

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


# =====================================================
# MANY-TO-MANY ASSOCIATION TABLE
# Chat sessions can contain multiple selected documents.
# A document can be used in multiple chat sessions.
# =====================================================

chat_session_documents = Table(
    "chat_session_documents",
    db.metadata,

    Column(
        "chat_session_id",
        db.Integer,
        ForeignKey(
            "chat_sessions.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    ),

    Column(
        "document_id",
        db.Integer,
        ForeignKey(
            "documents.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
)


# =====================================================
# 1. CHAT SESSION MODEL
# Stores individual AI conversations.
# =====================================================

class ChatSession(db.Model):

    __tablename__ = "chat_sessions"

    __table_args__ = (
        Index(
            "ix_chat_sessions_user_updated",
            "user_id",
            "updated_at"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    title = db.Column(
        db.String(255),
        nullable=False,
        default="New conversation"
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    is_archived = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now
    )

    # User relationship
    user = db.relationship(
        "User",
        backref=db.backref(
            "chat_sessions",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    # Chat messages relationship
    messages = db.relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChatMessage.created_at"
    )

    # Selected documents relationship
    documents = db.relationship(
        "Document",
        secondary=chat_session_documents,
        lazy="select"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "is_archived": self.is_archived,

            "document_ids": [
                document.id
                for document in self.documents
            ],

            "message_count": len(self.messages),

            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            ),

            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at else None
            )
        }

    def __repr__(self):
        return f"<ChatSession {self.id}: {self.title}>"


# =====================================================
# 2. CHAT MESSAGE MODEL
# Stores user questions and AI responses.
# =====================================================

class ChatMessage(db.Model):

    __tablename__ = "chat_messages"

    __table_args__ = (
        Index(
            "ix_chat_messages_session_created",
            "chat_session_id",
            "created_at"
        ),

        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="check_chat_message_role"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    chat_session_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "chat_sessions.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    model_name = db.Column(
        db.String(150),
        nullable=True
    )

    prompt_tokens = db.Column(
        db.Integer,
        nullable=True
    )

    completion_tokens = db.Column(
        db.Integer,
        nullable=True
    )

    response_time_ms = db.Column(
        db.Integer,
        nullable=True
    )

    sources = db.Column(
        JSON,
        nullable=True
    )

    extra_data = db.Column(
        JSON,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    # Parent chat session
    session = db.relationship(
        "ChatSession",
        back_populates="messages"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "chat_session_id": self.chat_session_id,
            "role": self.role,
            "content": self.content,
            "model_name": self.model_name,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "response_time_ms": self.response_time_ms,
            "sources": self.sources,
            "extra_data": self.extra_data,

            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            )
        }

    def __repr__(self):
        return f"<ChatMessage {self.id}: {self.role}>"


# =====================================================
# 3. DOCUMENT CHUNK MODEL
# Stores extracted PDF text chunks for RAG.
# =====================================================

class DocumentChunk(db.Model):

    __tablename__ = "document_chunks"

    __table_args__ = (

        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunk_index"
        ),

        Index(
            "ix_document_chunks_user_document",
            "user_id",
            "document_id"
        ),

        Index(
            "ix_document_chunks_embedding",
            "embedding_id"
        ),

        CheckConstraint(
            "chunk_index >= 0",
            name="check_chunk_index"
        ),

        CheckConstraint(
            "page_number IS NULL OR page_number >= 1",
            name="check_chunk_page"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    document_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "documents.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    chunk_index = db.Column(
        db.Integer,
        nullable=False
    )

    page_number = db.Column(
        db.Integer,
        nullable=True
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    embedding_id = db.Column(
        db.String(255),
        nullable=True
    )

    chunk_metadata = db.Column(
        JSON,
        nullable=True
    )

    token_count = db.Column(
        db.Integer,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    # User relationship
    user = db.relationship(
        "User",
        backref=db.backref(
            "document_chunks",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    # Document relationship
    document = db.relationship(
        "Document",
        backref=db.backref(
            "chunks",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    def to_dict(self):

        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "content": self.content,
            "embedding_id": self.embedding_id,
            "chunk_metadata": self.chunk_metadata,
            "token_count": self.token_count,

            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            )
        }

    def __repr__(self):
        return (
            f"<DocumentChunk {self.id}: "
            f"document={self.document_id}>"
        )
