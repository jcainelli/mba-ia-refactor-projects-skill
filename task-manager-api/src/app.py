from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from src.config.database import db
from src.config.settings import settings
from src.middlewares.error_handler import register_error_handlers
from src.models import Category, Task, User  # noqa: F401  (register mappers)
from src.views.auth_routes import auth_bp
from src.views.category_routes import category_bp
from src.views.report_routes import report_bp
from src.views.task_routes import task_bp
from src.views.user_routes import user_bp

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_app():
    app = Flask(__name__, instance_path=str(PROJECT_ROOT / "instance"))
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["DEBUG"] = settings.DEBUG

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(auth_bp)

    register_error_handlers(app)

    @app.route("/")
    def index():
        return jsonify({"message": "Task Manager API", "version": "1.0"}), 200

    @app.route("/health")
    def health():
        return (
            jsonify(
                {
                    "status": "ok",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
