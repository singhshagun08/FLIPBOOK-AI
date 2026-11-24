
from sqlalchemy import event
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()

migrate = Migrate()

jwt = JWTManager()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


def initialize_extensions(app):
    """Initialize all Flask extensions."""

    db.init_app(app)

    # Enable SQLite foreign-key enforcement.
    with app.app_context():
        engine = db.engine

        if engine.dialect.name == "sqlite":

            @event.listens_for(engine, "connect")
            def enable_sqlite_foreign_keys(
                dbapi_connection,
                connection_record
            ):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    migrate.init_app(
        app,
        db,
        compare_type=True
    )

    jwt.init_app(app)

    limiter.init_app(app)
