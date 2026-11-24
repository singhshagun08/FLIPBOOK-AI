
from datetime import datetime, timezone

from sqlalchemy import Index, CheckConstraint
from sqlalchemy.types import JSON

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class Translation(db.Model):

    __tablename__ = "translations"

    __table_args__ = (
        Index(
            "ix_translations_user_created",
            "user_id",
            "created_at"
        ),

        Index(
            "ix_translations_user_status",
            "user_id",
            "translation_status"
        ),

        CheckConstraint(
            "translation_status IN ('pending', 'processing', 'completed', 'failed')",
            name="check_translation_status"
        ),

        CheckConstraint(
            "page_count IS NULL OR page_count >= 0",
            name="check_translation_page_count"
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
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    source_language = db.Column(
        db.String(30),
        nullable=False
    )

    target_language = db.Column(
        db.String(30),
        nullable=False
    )

    translation_engine = db.Column(
        db.String(100),
        nullable=True
    )

    original_text = db.Column(
        db.Text,
        nullable=True
    )

    translated_text = db.Column(
        db.Text,
        nullable=True
    )

    translation_status = db.Column(
        db.String(30),
        nullable=False,
        default="pending"
    )

    translation_error = db.Column(
        db.Text,
        nullable=True
    )

    page_count = db.Column(
        db.Integer,
        nullable=True
    )

    translation_metadata = db.Column(
        JSON,
        nullable=True
    )

    exported_file_path = db.Column(
        db.String(1000),
        nullable=True
    )

    exported_file_format = db.Column(
        db.String(30),
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

    completed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    # Translation owner.
    user = db.relationship(
        "User",
        backref=db.backref(
            "translations",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    # Original PDF document.
    document = db.relationship(
        "Document",
        backref=db.backref(
            "translations",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "title": self.title,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "translation_engine": self.translation_engine,
            "original_text": self.original_text,
            "translated_text": self.translated_text,
            "translation_status": self.translation_status,
            "translation_error": self.translation_error,
            "page_count": self.page_count,
            "translation_metadata": self.translation_metadata,
            "exported_file_format": self.exported_file_format,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at else None
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at else None
            )
        }

    def __repr__(self):
        return f"<Translation {self.id}: {self.title}>"
