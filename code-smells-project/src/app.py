import logging
from flask import Flask
from flask_cors import CORS

from src.config.database import init_app as init_db_app, init_db
from src.config.settings import settings
from src.middlewares.error_handler import register_error_handlers
from src.views.admin_routes import admin_bp
from src.views.auth_routes import auth_bp
from src.views.health_routes import health_bp
from src.views.index_routes import index_bp
from src.views.pedido_routes import pedido_bp
from src.views.produto_routes import produto_bp
from src.views.relatorio_routes import relatorio_bp
from src.views.usuario_routes import usuario_bp


def create_app() -> Flask:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    app.config["JSON_SORT_KEYS"] = False

    CORS(app, origins=settings.CORS_ORIGINS)

    init_db_app(app)
    init_db()

    for bp in (index_bp, health_bp, produto_bp, usuario_bp, auth_bp,
               pedido_bp, relatorio_bp, admin_bp):
        app.register_blueprint(bp)

    register_error_handlers(app)
    return app


if __name__ == "__main__":
    create_app().run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
