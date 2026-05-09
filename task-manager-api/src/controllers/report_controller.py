from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select

from src.config.constants import (
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
    TERMINAL_TASK_STATUSES,
    VALID_TASK_STATUSES,
)
from src.config.database import db
from src.middlewares.error_handler import NotFoundError
from src.models.category import Category
from src.models.task import Task, aware_utc
from src.models.user import User


def summary():
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    total_tasks = db.session.execute(select(func.count(Task.id))).scalar_one()
    total_users = db.session.execute(select(func.count(User.id))).scalar_one()
    total_categories = db.session.execute(select(func.count(Category.id))).scalar_one()

    by_status = dict(
        db.session.execute(
            select(Task.status, func.count(Task.id)).group_by(Task.status)
        ).all()
    )
    by_priority = dict(
        db.session.execute(
            select(Task.priority, func.count(Task.id)).group_by(Task.priority)
        ).all()
    )

    overdue_rows = (
        db.session.execute(
            select(Task).filter(
                Task.due_date.is_not(None),
                Task.due_date < now,
                Task.status.notin_(TERMINAL_TASK_STATUSES),
            )
        )
        .scalars()
        .all()
    )
    overdue_list = [
        {
            "id": t.id,
            "title": t.title,
            "due_date": aware_utc(t.due_date).isoformat() if t.due_date else None,
            "days_overdue": (now - aware_utc(t.due_date)).days,
        }
        for t in overdue_rows
    ]

    recent_tasks = db.session.execute(
        select(func.count(Task.id)).filter(Task.created_at >= seven_days_ago)
    ).scalar_one()
    recent_done = db.session.execute(
        select(func.count(Task.id)).filter(
            Task.status == "done",
            Task.updated_at >= seven_days_ago,
        )
    ).scalar_one()

    user_stats_rows = db.session.execute(
        select(
            User.id,
            User.name,
            func.count(Task.id).label("total"),
            func.sum(case((Task.status == "done", 1), else_=0)).label("done"),
        )
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id, User.name)
    ).all()
    user_stats = []
    for uid, uname, total, done in user_stats_rows:
        total = total or 0
        done = done or 0
        user_stats.append(
            {
                "user_id": uid,
                "user_name": uname,
                "total_tasks": total,
                "completed_tasks": done,
                "completion_rate": round((done / total) * 100, 2) if total else 0,
            }
        )

    return {
        "generated_at": now.isoformat(),
        "overview": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "total_categories": total_categories,
        },
        "tasks_by_status": {status: by_status.get(status, 0) for status in VALID_TASK_STATUSES},
        "tasks_by_priority": {label: by_priority.get(value, 0) for value, label in PRIORITY_LABELS.items()},
        "overdue": {
            "count": len(overdue_list),
            "tasks": overdue_list,
        },
        "recent_activity": {
            "tasks_created_last_7_days": recent_tasks,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": user_stats,
    }


def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    now = datetime.now(timezone.utc)
    tasks = (
        db.session.execute(select(Task).filter_by(user_id=user_id)).scalars().all()
    )

    total = len(tasks)
    done = sum(1 for t in tasks if t.status == "done")
    pending = sum(1 for t in tasks if t.status == "pending")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    cancelled = sum(1 for t in tasks if t.status == "cancelled")
    overdue = sum(
        1
        for t in tasks
        if t.due_date
        and aware_utc(t.due_date) < now
        and t.status not in TERMINAL_TASK_STATUSES
    )
    high_priority = sum(1 for t in tasks if t.priority and t.priority <= 2)

    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": total,
            "done": done,
            "pending": pending,
            "in_progress": in_progress,
            "cancelled": cancelled,
            "overdue": overdue,
            "high_priority": high_priority,
            "completion_rate": round((done / total) * 100, 2) if total else 0,
        },
    }
