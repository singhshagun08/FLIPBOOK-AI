
from datetime import datetime, timezone

from sqlalchemy import Index, CheckConstraint, JSON

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class Document(db.Model):
    __tablename__ = "documents"

    __table_args__ = (
        Index(
            "ix_documents_user_created",
            "user_id",
            "created_at"
        ),
        Index(
            "ix_documents_user_status",
            "user_id",
            "processing_status"
        ),
        CheckConstraint(
            "file_size >= 0",
            name="check_document_file_size"
        ),
        CheckConstraint(
            "page_count IS NULL OR page_count >= 0",
            name="check_document_page_count"
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
    
    folder_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "folders.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    original_filename = db.Column(
        db.String(255),
        nullable=False
    )

    stored_filename = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )

    file_path = db.Column(
        db.String(1000),
        nullable=False
    )

    mime_type = db.Column(
        db.String(100),
        nullable=False,
        default="application/pdf"
    )

    file_size = db.Column(
        db.BigInteger,
        nullable=False
    )

    page_count = db.Column(
        db.Integer,
        nullable=True
    )

    processing_status = db.Column(
        db.String(30),
        nullable=False,
        default="pending",
        index=True
    )

    processing_error = db.Column(
        db.Text,
        nullable=True
    )

    extracted_metadata = db.Column(
        JSON,
        nullable=True
    )

    checksum = db.Column(
        db.String(64),
        nullable=True,
        index=True
    )

    is_favorite = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    description = db.Column(
        db.Text,
        nullable=True
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

    # Relationship with the document owner.
    user = db.relationship(
        "User",
        backref=db.backref(
            "documents",
            lazy="dynamic",
            passive_deletes=True
        )
    )
    
    folder = db.relationship(
        "Folder",
        back_populates="documents"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "page_count": self.page_count,
            "processing_status": self.processing_status,
            "processing_error": self.processing_error,
            "extracted_metadata": self.extracted_metadata,
            "checksum": self.checksum,
            "is_favorite": self.is_favorite,
            "description": self.description,
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
        return f"<Document {self.title}>"
