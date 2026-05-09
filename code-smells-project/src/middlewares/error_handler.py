import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500

    def __init__(self, message, status_code=None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = 404


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _handle_app_error(err):
        return jsonify({"erro": str(err), "sucesso": False}), err.status_code

    @app.errorhandler(HTTPException)
    def _handle_http_exception(err):
        return jsonify({"erro": err.description, "sucesso": False}), err.code

    @app.errorhandler(Exception)
    def _handle_unexpected(err):
        log.exception("Unexpected error: %s", err)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
