
import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")


def parse_origins(value: str) -> list[str]:
    return [
        origin.strip()
        for origin in value.split(",")
        if origin.strip()
    ]


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-this")
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "development-jwt-secret-change-this"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'flipbook.db').as_posix()}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True
    }

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["headers"]

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024

    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    GENERATED_FOLDER = str(BASE_DIR / "generated")

    ALLOWED_EXTENSIONS = {"pdf"}

    CORS_ORIGINS = parse_origins(
        os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173"
        )
    )

    OLLAMA_BASE_URL = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434"
    )

    OLLAMA_CHAT_MODEL = os.getenv(
        "OLLAMA_CHAT_MODEL",
        "llama3.2:3b"
    )

    OLLAMA_EMBEDDING_MODEL = os.getenv(
        "OLLAMA_EMBEDDING_MODEL",
        "nomic-embed-text"
    )

    CHROMA_PERSIST_DIRECTORY = os.getenv(
        "CHROMA_PERSIST_DIRECTORY",
        str(BASE_DIR / "chroma_db")
    )

    CHROMA_COLLECTION_NAME = os.getenv(
        "CHROMA_COLLECTION_NAME",
        "flipbook_documents"
    )

    AI_REQUEST_TIMEOUT = int(
        os.getenv("AI_REQUEST_TIMEOUT", "180")
    )

    PDF_MAX_PAGES = int(
        os.getenv("PDF_MAX_PAGES", "2000")
    )

    RATELIMIT_DEFAULT = "200 per day, 50 per hour"

    RATELIMIT_STORAGE_URI = os.getenv(
        "RATELIMIT_STORAGE_URI",
        "memory://"
    )

    JSON_SORT_KEYS = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)

    RATELIMIT_ENABLED = False
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
