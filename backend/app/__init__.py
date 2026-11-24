
import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

from app.config import CONFIG_MAP
from app.extensions import db,initialize_extensions,jwt
from app.routes import register_blueprints
from app.utils.responses import error_response


def create_app(config_name=None):
    """
    Create and configure the FLIPBOOK-AI Flask application.
    """

    app = Flask(__name__)

    environment = (
        config_name
        or os.getenv("FLASK_ENV", "development")
    ).lower()

    config_class = CONFIG_MAP.get(environment)

    if config_class is None:
        raise ValueError(
            f"Unsupported environment: {environment}"
        )

    app.config.from_object(config_class)

    if environment == "production":
        if (
            app.config["SECRET_KEY"].startswith("development")
            or app.config["JWT_SECRET_KEY"].startswith("development")
        ):
            raise RuntimeError(
                "Production requires secure SECRET_KEY and JWT_SECRET_KEY values."
            )

    Path(app.config["UPLOAD_FOLDER"]).mkdir(
        parents=True,
        exist_ok=True
    )

    Path(app.config["GENERATED_FOLDER"]).mkdir(
        parents=True,
        exist_ok=True
    )

    Path(app.config["CHROMA_PERSIST_DIRECTORY"]).mkdir(
        parents=True,
        exist_ok=True
    )

    initialize_extensions(app)
    from app.models import TokenBlocklist, User

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """
        Reject revoked JWTs and tokens issued before
        the user's current token version.
        """

        jti = jwt_payload["jti"]

        token = db.session.get(TokenBlocklist, jti)

        if token is not None:
            return True

        user_id = jwt_payload.get("sub")

        try:
            user = db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return True

        if user is None or not user.is_active:
            return True

        token_version = jwt_payload.get("token_version")

        if token_version != user.token_version:
            return True

        return False
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["CORS_ORIGINS"]
            }
        },
        supports_credentials=False
    )

    app.json.sort_keys = False

    # Import model modules so SQLAlchemy metadata
    # can discover them for database migrations.
    from app import models  # noqa: F401

    register_blueprints(app)

    @app.route("/", methods=["GET"])
    def index():
        return {
            "application": "FLIPBOOK-AI",
            "message": "Backend API is operational",
            "health_endpoint": "/api/health"
        }, 200

    @app.errorhandler(404)
    def not_found(error):
        return error_response(
            message="The requested resource was not found",
            status_code=404
        )

    @app.errorhandler(405)
    def method_not_allowed(error):
        return error_response(
            message="HTTP method not allowed",
            status_code=405
        )

    @app.errorhandler(413)
    def file_too_large(error):
        return error_response(
            message="Uploaded file exceeds the maximum allowed size",
            status_code=413
        )

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        app.logger.exception("Database operation failed")

        return error_response(
            message="A database operation failed",
            status_code=500
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.exception("Internal server error")

        return error_response(
            message="An internal server error occurred",
            status_code=500
        )

    return app
