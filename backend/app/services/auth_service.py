
import re

from email_validator import validate_email, EmailNotValidError

from app.extensions import db
from app.models import User


def normalize_email(email):
    """Normalize and validate an email address."""

    if not isinstance(email, str) or not email.strip():
        raise ValueError("Email is required.")

    try:
        result = validate_email(
            email.strip(),
            check_deliverability=False
        )
        return result.normalized.lower()

    except EmailNotValidError:
        raise ValueError("Please provide a valid email address.")


def normalize_username(username):
    """Validate and normalize a username."""

    if not isinstance(username, str):
        raise ValueError("Username is required.")

    username = username.strip().lower()

    if not re.fullmatch(r"[a-z0-9_]{3,80}", username):
        raise ValueError(
            "Username must contain 3-80 characters "
            "using letters, numbers, or underscores."
        )

    return username


def validate_full_name(full_name):
    """Validate a user's full name."""

    if not isinstance(full_name, str):
        raise ValueError("Full name is required.")

    full_name = full_name.strip()

    if not full_name or len(full_name) > 150:
        raise ValueError(
            "Full name must contain 1-150 characters."
        )

    return full_name


def validate_password(password):
    """Validate password requirements."""

    if not isinstance(password, str):
        raise ValueError("Password is required.")

    if len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    return password


def register_user(full_name, username, email, password):
    """Create a new user account."""

    full_name = validate_full_name(full_name)
    username = normalize_username(username)
    email = normalize_email(email)
    password = validate_password(password)

    existing_username = db.session.query(User.id).filter_by(
        username=username
    ).first()

    if existing_username:
        raise ValueError("Username is already registered.")

    existing_email = db.session.query(User.id).filter_by(
        email=email
    ).first()

    if existing_email:
        raise ValueError("Email is already registered.")

    user = User(
        full_name=full_name,
        username=username,
        email=email
    )

    user.set_password(password)

    db.session.add(user)

    return user


def authenticate_user(identifier, password):
    """Authenticate using email or username."""

    if not isinstance(identifier, str) or not identifier.strip():
        return None

    if not isinstance(password, str) or not password:
        return None

    identifier = identifier.strip().lower()

    user = User.query.filter(
        db.or_(
            User.email == identifier,
            User.username == identifier
        )
    ).first()

    if user is None:
        return None

    if not user.is_active:
        return None

    if not user.check_password(password):
        return None

    return user
