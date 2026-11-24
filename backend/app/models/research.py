
from datetime import datetime, timezone

from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    Index,
    CheckConstraint
)
from sqlalchemy.types import JSON

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


# =====================================================
# ASSOCIATION TABLE
# Connects research projects with multiple documents.
# =====================================================

research_project_documents = Table(
    "research_project_documents",
    db.metadata,

    Column(
        "research_project_id",
        db.Integer,
        ForeignKey(
            "research_projects.id",
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
# 1. RESEARCH PROJECT MODEL
# Organizes individual research projects.
# =====================================================

class ResearchProject(db.Model):

    __tablename__ = "research_projects"

    __table_args__ = (
        Index(
            "ix_research_projects_user_updated",
            "user_id",
            "updated_at"
        ),

        CheckConstraint(
            "status IN ('planning', 'active', 'completed', 'archived')",
            name="check_research_project_status"
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
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    research_question = db.Column(
        db.Text,
        nullable=True
    )

    objectives = db.Column(
        JSON,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="planning"
    )

    subject_area = db.Column(
        db.String(150),
        nullable=True
    )

    tags = db.Column(
        JSON,
        nullable=True
    )

    start_date = db.Column(
        db.Date,
        nullable=True
    )

    target_completion_date = db.Column(
        db.Date,
        nullable=True
    )

    completed_at = db.Column(
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

    # Project owner.
    user = db.relationship(
        "User",
        backref=db.backref(
            "research_projects",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    # Documents attached to this research project.
    documents = db.relationship(
        "Document",
        secondary=research_project_documents,
        lazy="select"
    )

    # Research notes belonging to this project.
    notes = db.relationship(
        "ResearchNote",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ResearchNote.created_at.desc()"
    )

    def to_dict(self, include_notes=False):
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "research_question": self.research_question,
            "objectives": self.objectives,
            "status": self.status,
            "subject_area": self.subject_area,
            "tags": self.tags,
            "start_date": (
                self.start_date.isoformat()
                if self.start_date else None
            ),
            "target_completion_date": (
                self.target_completion_date.isoformat()
                if self.target_completion_date else None
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at else None
            ),
            "document_ids": [
                document.id
                for document in self.documents
            ],
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at else None
            )
        }

        if include_notes:
            result["notes"] = [
                note.to_dict()
                for note in self.notes
            ]

        return result

    def __repr__(self):
        return f"<ResearchProject {self.id}: {self.title}>"


# =====================================================
# 2. RESEARCH NOTE MODEL
# Stores research findings and citation records.
# =====================================================

class ResearchNote(db.Model):

    __tablename__ = "research_notes"

    __table_args__ = (
        Index(
            "ix_research_notes_user_project",
            "user_id",
            "project_id"
        ),

        Index(
            "ix_research_notes_document",
            "document_id"
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

    project_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "research_projects.id",
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

    content = db.Column(
        db.Text,
        nullable=False
    )

    note_type = db.Column(
        db.String(50),
        nullable=False,
        default="general"
    )

    citations = db.Column(
        JSON,
        nullable=True
    )

    source_reference = db.Column(
        db.String(500),
        nullable=True
    )

    tags = db.Column(
        JSON,
        nullable=True
    )

    is_pinned = db.Column(
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

    # Note owner.
    user = db.relationship(
        "User",
        backref=db.backref(
            "research_notes",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    # Parent research project.
    project = db.relationship(
        "ResearchProject",
        back_populates="notes"
    )

    # Optional source document.
    document = db.relationship(
        "Document",
        backref=db.backref(
            "research_notes",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "document_id": self.document_id,
            "title": self.title,
            "content": self.content,
            "note_type": self.note_type,
            "citations": self.citations,
            "source_reference": self.source_reference,
            "tags": self.tags,
            "is_pinned": self.is_pinned,
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
        return f"<ResearchNote {self.id}: {self.title}>"
