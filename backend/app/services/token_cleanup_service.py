from datetime import datetime, timezone

from sqlalchemy import delete

from app.extensions import db
from app.models import TokenBlocklist


def cleanup_expired_tokens():
    """
    Delete revoked JWT records whose expiry time has passed.

    Returns the number of deleted records.
    """

    now = datetime.now(timezone.utc)

    statement = delete(TokenBlocklist).where(
        TokenBlocklist.expires_at < now
    )

    result = db.session.execute(statement)
    db.session.commit()

    return result.rowcount or 0