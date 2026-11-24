from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from flask import Blueprint, request , current_app

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_jwt,
    jwt_required
)

from app.extensions import db, limiter
from app.models import User, TokenBlocklist

from app.services.auth_service import (
    register_user,
    authenticate_user,
    validate_full_name,
    normalize_username,
    normalize_email,
    validate_password
)

from app.utils.responses import success_response, error_response


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def get_json_data():
    """Return validated JSON request data."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None

    return data


def create_user_tokens(user):
    """Create an access and refresh token pair."""

    claims = {
        "token_type": "access",
        "token_version": user.token_version
    }

    refresh_claims = {
        "token_type": "refresh",
        "token_version": user.token_version
    }

    return (
        create_access_token(
            identity=str(user.id),
            additional_claims=claims
        ),
        create_refresh_token(
            identity=str(user.id),
            additional_claims=refresh_claims
        )
    )


def revoke_token(jwt_payload):
    """Store a JWT ID in the database blocklist."""

    jti = jwt_payload["jti"]

    existing = db.session.get(TokenBlocklist, jti)

    if existing:
        return

    user_id = int(jwt_payload["sub"])

    token = TokenBlocklist(
        jti=jti,
        user_id=user_id,
        token_type=jwt_payload.get("type", "unknown"),
        expires_at=datetime.fromtimestamp(
            jwt_payload["exp"],
            tz=timezone.utc
        )
    )

    db.session.add(token)


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():

    data = get_json_data()

    if data is None:
        return error_response(
            message="A valid JSON request body is required.",
            status_code=400
        )

    try:
        user = register_user(
            full_name=data.get("full_name"),
            username=data.get("username"),
            email=data.get("email"),
            password=data.get("password")
        )

        db.session.add(user)
        db.session.commit()

        return success_response(
            message="Account registered successfully.",
            data={"user": user.to_dict()},
            status_code=201
        )

    except ValueError as exc:
        db.session.rollback()
        return error_response(
            message=str(exc),
            status_code=400
        )

    except IntegrityError:
        db.session.rollback()
        return error_response(
            message="Username or email is already registered.",
            status_code=409
        )

    except Exception:
        db.session.rollback()
        auth_bp.logger.exception("Registration failed")

        return error_response(
            message="Registration failed.",
            status_code=500
        )


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():

    data = get_json_data()

    if data is None:
        return error_response(
            message="A valid JSON request body is required.",
            status_code=400
        )

    identifier = data.get("identifier")
    password = data.get("password")

    if not identifier or not password:
        return error_response(
            message="Username/email and password are required.",
            status_code=400
        )

    user = authenticate_user(identifier, password)

    if user is None:
        return error_response(
            message="Invalid credentials or inactive account.",
            status_code=401
        )

    access_token, refresh_token = create_user_tokens(user)

    return success_response(
        message="Login successful.",
        data={
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
        }
    )


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():

    old_token = get_jwt()
    user_id = get_jwt_identity()

    if old_token.get("token_type") != "refresh":
        return error_response(
            message="A valid refresh token is required.",
            status_code=401
        )

    try:
        user = db.session.get(User, int(user_id))

        if user is None or not user.is_active:
            return error_response(
                message="User account is unavailable.",
                status_code=401
            )

        # Revoke the refresh token being used.
        revoke_token(old_token)

        # Create a completely new token pair.
        access_token, refresh_token = create_user_tokens(user)

        # Commit revocation before returning the new pair.
        db.session.commit()

        return success_response(
            message="Tokens refreshed successfully.",
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer"
            }
        )

    except Exception:
        db.session.rollback()
        auth_bp.logger.exception("Token refresh failed")

        return error_response(
            message="Token refresh failed.",
            status_code=500
        )


@auth_bp.route("/logout", methods=["POST"])
@jwt_required(verify_type=False)
def logout():

    try:
        current_token = get_jwt()

        revoke_token(current_token)
        db.session.commit()

        return success_response(
            message="Logout successful. Token revoked."
        )

    except Exception:
        db.session.rollback()
        auth_bp.logger.exception("Logout failed")

        return error_response(
            message="Logout failed.",
            status_code=500
        )


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():

    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    if user is None or not user.is_active:
        return error_response(
            message="User account not found.",
            status_code=404
        )

    return success_response(
        message="Profile retrieved successfully.",
        data={"user": user.to_dict()}
    )


@auth_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_profile():

    data = get_json_data()

    if data is None:
        return error_response(
            message="A valid JSON request body is required.",
            status_code=400
        )

    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    if user is None or not user.is_active:
        return error_response(
            message="User account not found.",
            status_code=404
        )

    try:
        if "full_name" in data:
            user.full_name = validate_full_name(data["full_name"])

        if "username" in data:
            username = normalize_username(data["username"])

            existing = User.query.filter(
                User.username == username,
                User.id != user.id
            ).first()

            if existing:
                db.session.rollback()
                return error_response(
                    message="Username is already registered.",
                    status_code=409
                )

            user.username = username

        if "email" in data:
            email = normalize_email(data["email"])

            existing = User.query.filter(
                User.email == email,
                User.id != user.id
            ).first()

            if existing:
                db.session.rollback()
                return error_response(
                    message="Email is already registered.",
                    status_code=409
                )

            user.email = email

        db.session.commit()

        return success_response(
            message="Profile updated successfully.",
            data={"user": user.to_dict()}
        )

    except ValueError as exc:
        db.session.rollback()
        return error_response(
            message=str(exc),
            status_code=400
        )

    except IntegrityError:
        db.session.rollback()
        return error_response(
            message="Username or email is already registered.",
            status_code=409
        )

    except Exception:
        db.session.rollback()
        auth_bp.logger.exception("Profile update failed")

        return error_response(
            message="Profile update failed.",
            status_code=500
        )


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():

    data = get_json_data()

    if data is None:
        return error_response(
            message="A valid JSON request body is required.",
            status_code=400
        )

    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password or not new_password:
        return error_response(
            message="Current and new passwords are required.",
            status_code=400
        )

    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    if user is None or not user.is_active:
        return error_response(
            message="User account not found.",
            status_code=404
        )

    if not user.check_password(current_password):
        return error_response(
            message="Current password is incorrect.",
            status_code=400
        )

    try:
        validate_password(new_password)

        user.set_password(new_password)

        # Invalidate every previously issued token.
        user.token_version += 1

        db.session.commit()

        return success_response(
            message="Password changed successfully. Please log in again."
        )

    except ValueError as exc:
        db.session.rollback()
        return error_response(
            message=str(exc),
            status_code=400
        )

    except Exception:
        db.session.rollback()
        auth_bp.logger.exception("Password change failed")

        return error_response(
            message="Password change failed.",
            status_code=500
        )