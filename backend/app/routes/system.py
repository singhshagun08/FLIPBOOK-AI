
from flask import Blueprint, current_app
from sqlalchemy import text
from app.extensions import db
from app.utils.responses import success_response, error_response

system_bp = Blueprint("system", __name__)


@system_bp.route("/health", methods=["GET"])
def health_check():
    database_status = "healthy"

    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        current_app.logger.exception(
            "Database health check failed"
        )
        database_status = "unavailable"

    overall_status = (
        "healthy"
        if database_status == "healthy"
        else "degraded"
    )

    payload = {
        "application": "FLIPBOOK-AI",
        "status": overall_status,
        "services": {
            "database": database_status
        }
    }

    if overall_status == "healthy":
        return success_response(
            message="FLIPBOOK-AI backend is running",
            data=payload,
            status_code=200
        )

    return error_response(
        message="One or more backend services are unavailable",
        errors=payload,
        status_code=503
    )
