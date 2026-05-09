import logging

from sqlalchemy import func, select, update

from src.config.constants import DEFAULT_CATEGORY_COLOR
from src.config.database import db
from src.middlewares.error_handler import BadRequestError, NotFoundError
from src.models.category import Category
from src.models.task import Task

log = logging.getLogger(__name__)


def list_categories():
    rows = db.session.execute(
        select(Category, func.count(Task.id))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
    ).all()
    result = []
    for cat, task_count in rows:
        data = cat.to_dict()
        data["task_count"] = task_count
        result.append(data)
    return result


def create_category(data):
    name = data.get("name")
    if not name:
        raise BadRequestError("Nome é obrigatório")
    cat = Category(
        name=name,
        description=data.get("description", ""),
        color=data.get("color", DEFAULT_CATEGORY_COLOR),
    )
    db.session.add(cat)
    db.session.commit()
    log.info("category.created id=%s", cat.id)
    return cat.to_dict()


def update_category(cat_id, data):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise NotFoundError("Categoria não encontrada")
    if "name" in data:
        cat.name = data["name"]
    if "description" in data:
        cat.description = data["description"]
    if "color" in data:
        cat.color = data["color"]
    db.session.commit()
    return cat.to_dict()


def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise NotFoundError("Categoria não encontrada")
    db.session.execute(
        update(Task).where(Task.category_id == cat_id).values(category_id=None)
    )
    db.session.delete(cat)
    db.session.commit()
    log.info("category.deleted id=%s", cat_id)
