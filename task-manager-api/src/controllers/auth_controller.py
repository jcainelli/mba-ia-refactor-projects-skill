import logging

from sqlalchemy import select

from src.config.database import db
from src.middlewares.error_handler import (
    BadRequestError,
    ForbiddenError,
    UnauthorizedError,
)
from src.models.user import User
from src.services.auth_service import issue_token

log = logging.getLogger(__name__)


def login(data):
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise BadRequestError("Email e senha são obrigatórios")

    user = db.session.execute(select(User).filter_by(email=email)).scalar_one_or_none()
    if not user or not user.check_password(password):
        raise UnauthorizedError("Credenciais inválidas")
    if not user.active:
        raise ForbiddenError("Usuário inativo")

    log.info("auth.login id=%s", user.id)
    return {
        "message": "Login realizado com sucesso",
        "user": user.to_public_dict(),
        "token": issue_token(user.id, user.role),
    }
