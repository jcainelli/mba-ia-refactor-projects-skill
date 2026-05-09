import logging
import re

from sqlalchemy import select

from src.config.constants import MIN_PASSWORD_LENGTH, VALID_USER_ROLES
from src.config.database import db
from src.middlewares.error_handler import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from src.models.task import Task
from src.models.user import User

log = logging.getLogger(__name__)
EMAIL_RE = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")


def _validate_email(email):
    if not email or not EMAIL_RE.match(email):
        raise BadRequestError("Email inválido")


def _validate_password(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        raise BadRequestError(
            f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres"
        )


def _validate_role(role):
    if role not in VALID_USER_ROLES:
        raise BadRequestError("Role inválido")


def list_users():
    users = db.session.execute(select(User)).scalars().all()
    return [
        {**u.to_public_dict(), "task_count": len(u.tasks)} for u in users
    ]


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    tasks = (
        db.session.execute(select(Task).filter_by(user_id=user_id)).scalars().all()
    )
    data = user.to_public_dict()
    data["tasks"] = [t.to_dict() for t in tasks]
    return data


def create_user(data):
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")

    if not name:
        raise BadRequestError("Nome é obrigatório")
    if not email:
        raise BadRequestError("Email é obrigatório")
    if not password:
        raise BadRequestError("Senha é obrigatória")
    _validate_email(email)
    _validate_password(password)
    _validate_role(role)

    existing = db.session.execute(select(User).filter_by(email=email)).scalar_one_or_none()
    if existing:
        raise ConflictError("Email já cadastrado")

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    log.info("user.created id=%s", user.id)
    return user.to_public_dict()


def update_user(user_id, data):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        _validate_email(data["email"])
        existing = db.session.execute(
            select(User).filter_by(email=data["email"])
        ).scalar_one_or_none()
        if existing and existing.id != user_id:
            raise ConflictError("Email já cadastrado")
        user.email = data["email"]
    if "password" in data:
        _validate_password(data["password"])
        user.set_password(data["password"])
    if "role" in data:
        _validate_role(data["role"])
        user.role = data["role"]
    if "active" in data:
        user.active = bool(data["active"])

    db.session.commit()
    return user.to_public_dict()


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    tasks = (
        db.session.execute(select(Task).filter_by(user_id=user_id)).scalars().all()
    )
    for task in tasks:
        db.session.delete(task)
    db.session.delete(user)
    db.session.commit()
    log.info("user.deleted id=%s", user_id)
