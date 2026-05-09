import logging
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from src.config.constants import TERMINAL_TASK_STATUSES
from src.config.database import db
from src.middlewares.error_handler import BadRequestError, NotFoundError
from src.models.category import Category
from src.models.task import Task
from src.models.user import User

log = logging.getLogger(__name__)


def _serialize(task, with_relations=False):
    data = task.to_dict()
    data["overdue"] = task.is_overdue()
    if with_relations:
        data["user_name"] = task.user.name if task.user else None
        data["category_name"] = task.category.name if task.category else None
    return data


def _parse_due_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        raise BadRequestError("Formato de data inválido. Use YYYY-MM-DD")
    return parsed.replace(tzinfo=timezone.utc)


def _normalize_tags(value):
    if value is None:
        return None
    if isinstance(value, list):
        return ",".join(str(t) for t in value)
    return str(value)


def _require_user(user_id):
    if user_id is not None and not db.session.get(User, user_id):
        raise NotFoundError("Usuário não encontrado")


def _require_category(category_id):
    if category_id is not None and not db.session.get(Category, category_id):
        raise NotFoundError("Categoria não encontrada")


def list_tasks():
    stmt = select(Task).options(joinedload(Task.user), joinedload(Task.category))
    tasks = db.session.execute(stmt).scalars().all()
    return [_serialize(t, with_relations=True) for t in tasks]


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    return _serialize(task)


def create_task(data):
    _require_user(data.get("user_id"))
    _require_category(data.get("category_id"))

    task = Task(
        title=data["title"],
        description=data.get("description", ""),
        status=data.get("status", "pending"),
        priority=data.get("priority"),
        user_id=data.get("user_id"),
        category_id=data.get("category_id"),
        due_date=_parse_due_date(data.get("due_date")),
        tags=_normalize_tags(data.get("tags")),
    )
    db.session.add(task)
    db.session.commit()
    log.info("task.created id=%s title=%s", task.id, task.title)
    return _serialize(task)


def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task não encontrada")

    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "status" in data:
        task.status = data["status"]
    if "priority" in data:
        task.priority = data["priority"]
    if "user_id" in data:
        _require_user(data["user_id"])
        task.user_id = data["user_id"]
    if "category_id" in data:
        _require_category(data["category_id"])
        task.category_id = data["category_id"]
    if "due_date" in data:
        task.due_date = _parse_due_date(data["due_date"])
    if "tags" in data:
        task.tags = _normalize_tags(data["tags"])

    db.session.commit()
    log.info("task.updated id=%s", task.id)
    return _serialize(task)


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    db.session.delete(task)
    db.session.commit()
    log.info("task.deleted id=%s", task_id)


def search_tasks(query, status, priority, user_id):
    stmt = select(Task)
    if query:
        like = f"%{query}%"
        stmt = stmt.filter(or_(Task.title.like(like), Task.description.like(like)))
    if status:
        stmt = stmt.filter(Task.status == status)
    if priority:
        stmt = stmt.filter(Task.priority == _coerce_int(priority, "priority"))
    if user_id:
        stmt = stmt.filter(Task.user_id == _coerce_int(user_id, "user_id"))
    tasks = db.session.execute(stmt).scalars().all()
    return [t.to_dict() for t in tasks]


def task_stats():
    counts_by_status = dict(
        db.session.execute(
            select(Task.status, func.count(Task.id)).group_by(Task.status)
        ).all()
    )
    total = sum(counts_by_status.values())
    done = counts_by_status.get("done", 0)

    overdue_count = db.session.execute(
        select(func.count(Task.id)).filter(
            Task.due_date.is_not(None),
            Task.due_date < datetime.now(timezone.utc),
            Task.status.notin_(TERMINAL_TASK_STATUSES),
        )
    ).scalar_one()

    return {
        "total": total,
        "pending": counts_by_status.get("pending", 0),
        "in_progress": counts_by_status.get("in_progress", 0),
        "done": done,
        "cancelled": counts_by_status.get("cancelled", 0),
        "overdue": overdue_count,
        "completion_rate": round((done / total) * 100, 2) if total else 0,
    }


def list_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    tasks = db.session.execute(select(Task).filter_by(user_id=user_id)).scalars().all()
    return [_serialize(t) for t in tasks]


def _coerce_int(value, name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise BadRequestError(f"{name} deve ser inteiro")
