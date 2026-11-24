
from datetime import datetime, timezone

from sqlalchemy import Index, CheckConstraint

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class Audiobook(db.Model):

    __tablename__ = "audiobooks"

    __table_args__ = (
        Index(
            "ix_audiobooks_user_created",
            "user_id",
            "created_at"
        ),

        Index(
            "ix_audiobooks_user_status",
            "user_id",
            "generation_status"
        ),

        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="check_audiobook_duration"
        ),

        CheckConstraint(
            "playback_position >= 0",
            name="check_audiobook_position"
        ),

        CheckConstraint(
            "playback_speed > 0",
            name="check_audiobook_speed"
        ),

        CheckConstraint(
            "generation_status IN ('pending', 'processing', 'completed', 'failed')",
            name="check_audiobook_status"
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

    tts_engine = db.Column(
        db.String(100),
        nullable=False,
        default="coqui"
    )

    voice_name = db.Column(
        db.String(150),
        nullable=True
    )

    language = db.Column(
        db.String(30),
        nullable=False,
        default="en"
    )

    audio_format = db.Column(
        db.String(20),
        nullable=False,
        default="wav"
    )

    audio_file_path = db.Column(
        db.String(1000),
        nullable=True
    )

    audio_file_size = db.Column(
        db.BigInteger,
        nullable=True
    )

    duration_seconds = db.Column(
        db.Float,
        nullable=True
    )

    generation_status = db.Column(
        db.String(30),
        nullable=False,
        default="pending"
    )

    generation_error = db.Column(
        db.Text,
        nullable=True
    )

    playback_position = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    playback_speed = db.Column(
        db.Float,
        nullable=False,
        default=1.0
    )

    is_completed = db.Column(
        db.Boolean,
        nullable=False,
        default=False
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

    # Audiobook owner.
    user = db.relationship(
        "User",
        backref=db.backref(
            "audiobooks",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    # Source PDF document.
    document = db.relationship(
        "Document",
        backref=db.backref(
            "audiobooks",
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
            "tts_engine": self.tts_engine,
            "voice_name": self.voice_name,
            "language": self.language,
            "audio_format": self.audio_format,
            "audio_file_size": self.audio_file_size,
            "duration_seconds": self.duration_seconds,
            "generation_status": self.generation_status,
            "generation_error": self.generation_error,
            "playback_position": self.playback_position,
            "playback_speed": self.playback_speed,
            "is_completed": self.is_completed,
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at else None
            ),
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
        return f"<Audiobook {self.id}: {self.title}>"
