
from datetime import datetime, timezone

from sqlalchemy import Index, CheckConstraint
from sqlalchemy.types import JSON

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


# =====================================================
# 1. STUDY SESSION MODEL
# Tracks user activity and study time.
# =====================================================

class StudySession(db.Model):

    __tablename__ = "study_sessions"

    __table_args__ = (
        Index(
            "ix_study_sessions_user_started",
            "user_id",
            "started_at"
        ),

        Index(
            "ix_study_sessions_user_type",
            "user_id",
            "session_type"
        ),

        CheckConstraint(
            "duration_seconds >= 0",
            name="check_study_duration"
        ),

        CheckConstraint(
            "session_type IN ('reading', 'learning', 'research', 'quiz', 'general')",
            name="check_study_session_type"
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

    session_type = db.Column(
        db.String(30),
        nullable=False,
        default="general"
    )

    title = db.Column(
        db.String(255),
        nullable=True
    )

    started_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    ended_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    duration_seconds = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    activity_metadata = db.Column(
        JSON,
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
            "study_sessions",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    document = db.relationship(
        "Document",
        backref=db.backref(
            "study_sessions",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "session_type": self.session_type,
            "title": self.title,
            "started_at": (
                self.started_at.isoformat()
                if self.started_at else None
            ),
            "ended_at": (
                self.ended_at.isoformat()
                if self.ended_at else None
            ),
            "duration_seconds": self.duration_seconds,
            "activity_metadata": self.activity_metadata,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            )
        }

    def __repr__(self):
        return f"<StudySession {self.id}: {self.session_type}>"


# =====================================================
# 2. USER SETTINGS MODEL
# Stores individual application preferences.
# =====================================================

class UserSettings(db.Model):

    __tablename__ = "user_settings"

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
        unique=True,
        index=True
    )

    # Appearance preferences
    theme = db.Column(
        db.String(30),
        nullable=False,
        default="system"
    )

    font_size = db.Column(
        db.String(20),
        nullable=False,
        default="medium"
    )

    reading_mode = db.Column(
        db.String(30),
        nullable=False,
        default="continuous"
    )

    # Language preferences
    interface_language = db.Column(
        db.String(20),
        nullable=False,
        default="en"
    )

    translation_language = db.Column(
        db.String(20),
        nullable=False,
        default="en"
    )

    # Reader preferences
    default_reading_speed = db.Column(
        db.Float,
        nullable=False,
        default=1.0
    )

    auto_bookmark = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # Notification preferences
    email_notifications = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    study_reminders = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # AI preferences
    preferred_ai_model = db.Column(
        db.String(150),
        nullable=True
    )

    preferred_tts_engine = db.Column(
        db.String(100),
        nullable=True,
        default="coqui"
    )

    # Additional customizable preferences
    preferences = db.Column(
        JSON,
        nullable=True,
        default=dict
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
            "settings",
            uselist=False,
            cascade="all, delete-orphan",
            passive_deletes=True
        )
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "theme": self.theme,
            "font_size": self.font_size,
            "reading_mode": self.reading_mode,
            "interface_language": self.interface_language,
            "translation_language": self.translation_language,
            "default_reading_speed": self.default_reading_speed,
            "auto_bookmark": self.auto_bookmark,
            "email_notifications": self.email_notifications,
            "study_reminders": self.study_reminders,
            "preferred_ai_model": self.preferred_ai_model,
            "preferred_tts_engine": self.preferred_tts_engine,
            "preferences": self.preferences,
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
        return f"<UserSettings user_id={self.user_id}>"
