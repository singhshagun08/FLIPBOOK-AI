
from datetime import datetime, timezone

from sqlalchemy import Index, UniqueConstraint

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class Folder(db.Model):
    __tablename__ = "folders"

    __table_args__ = (
        Index(
            "ix_folders_user_created",
            "user_id",
            "created_at"
        ),
        Index(
            "ix_folders_parent",
            "parent_folder_id"
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

    name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    parent_folder_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "folders.id",
            ondelete="CASCADE"
        ),
        nullable=True
    )

    color = db.Column(
        db.String(20),
        nullable=False,
        default="#64748b"
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

    # Folder owner.
    user = db.relationship(
        "User",
        backref=db.backref(
            "folders",
            lazy="dynamic",
            passive_deletes=True
        )
    )

    # Parent-child folder hierarchy.
    parent = db.relationship(
        "Folder",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_folder_id]
    )

    children = db.relationship(
        "Folder",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys=[parent_folder_id]
    )

    # Documents contained in this folder.
    documents = db.relationship(
        "Document",
        back_populates="folder",
        passive_deletes=True
    )

    def to_dict(self, include_children=False):
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "parent_folder_id": self.parent_folder_id,
            "color": self.color,
            "document_count": len(self.documents),
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at else None
            )
        }

        if include_children:
            result["children"] = [
                child.to_dict(include_children=True)
                for child in self.children
            ]

        return result

    def __repr__(self):
        return f"<Folder {self.name}>"
