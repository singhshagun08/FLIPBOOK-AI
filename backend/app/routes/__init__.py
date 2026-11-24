from app.routes.system import system_bp
from app.routes.auth import auth_bp
from app.routes.documents import documents_bp
from app.routes.folders import folders_bp
from app.routes.chat import chat_bp
from app.routes.learning import learning_bp
from app.routes.flashcards import flashcards_bp


def register_blueprints(app):
    app.register_blueprint(system_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(documents_bp, url_prefix="/api/documents")
    app.register_blueprint(folders_bp, url_prefix="/api/folders")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(learning_bp, url_prefix="/api/learning")
    app.register_blueprint(flashcards_bp, url_prefix="/api/learning")