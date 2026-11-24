
from datetime import datetime, timezone

from sqlalchemy import (
    Index,
    UniqueConstraint,
    CheckConstraint
)

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class ReadingProgress(db.Model):
    __tablename__ = "reading_progress"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "document_id",
            name="uq_reading_progress_user_document"
        ),
        CheckConstraint(
            "current_page >= 1",
            name="check_reading_current_page"
        ),
        CheckConstraint(
            "total_read_seconds >= 0",
            name="check_reading_time"
        ),
        Index(
            "ix_reading_progress_user_updated",
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
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    current_page = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    total_pages = db.Column(
        db.Integer,
        nullable=True
    )

    progress_percentage = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    total_read_seconds = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    is_completed = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    last_read_at = db.Column(
        db.DateTime(timezone=True),
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

    user = db.relationship(
        "User",
        backref=db.backref(
            "reading_progress",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    document = db.relationship(
        "Document",
        backref=db.backref(
            "reading_progress",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "progress_percentage": self.progress_percentage,
            "total_read_seconds": self.total_read_seconds,
            "is_completed": self.is_completed,
            "last_read_at": (
                self.last_read_at.isoformat()
                if self.last_read_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at else None
            )
        }


class Bookmark(db.Model):
    __tablename__ = "bookmarks"

    __table_args__ = (
        Index(
            "ix_bookmarks_user_document",
            "user_id",
            "document_id"
        ),
        CheckConstraint(
            "page_number >= 1",
            name="check_bookmark_page"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    page_number = db.Column(
        db.Integer,
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=True
    )

    note = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "bookmarks",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    document = db.relationship(
        "Document",
        backref=db.backref(
            "bookmarks",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "title": self.title,
            "note": self.note,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            )
        }


class Highlight(db.Model):
    __tablename__ = "highlights"

    __table_args__ = (
        Index(
            "ix_highlights_user_document_page",
            "user_id",
            "document_id",
            "page_number"
        ),
        CheckConstraint(
            "page_number >= 1",
            name="check_highlight_page"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    page_number = db.Column(
        db.Integer,
        nullable=False
    )

    selected_text = db.Column(
        db.Text,
        nullable=False
    )

    color = db.Column(
        db.String(30),
        nullable=False,
        default="yellow"
    )

    start_offset = db.Column(
        db.Integer,
        nullable=True
    )

    end_offset = db.Column(
        db.Integer,
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

    user = db.relationship(
        "User",
        backref=db.backref(
            "highlights",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    document = db.relationship(
        "Document",
        backref=db.backref(
            "highlights",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "selected_text": self.selected_text,
            "color": self.color,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            )
        }


class Annotation(db.Model):
    __tablename__ = "annotations"

    __table_args__ = (
        Index(
            "ix_annotations_user_document_page",
            "user_id",
            "document_id",
            "page_number"
        ),
        CheckConstraint(
            "page_number >= 1",
            name="check_annotation_page"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    page_number = db.Column(
        db.Integer,
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=True
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    selected_text = db.Column(
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

    user = db.relationship(
        "User",
        backref=db.backref(
            "annotations",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    document = db.relationship(
        "Document",
        backref=db.backref(
            "annotations",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "title": self.title,
            "content": self.content,
            "selected_text": self.selected_text,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at else None
            )
        }
