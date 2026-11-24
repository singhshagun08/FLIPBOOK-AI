from datetime import datetime, timezone

from app.extensions import db


class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"

    jti = db.Column(
        db.String(36),
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    token_type = db.Column(
        db.String(20),
        nullable=False
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True
    )

    revoked_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<TokenBlocklist {self.jti}>"