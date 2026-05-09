import logging
import smtplib
from datetime import datetime, timezone

from src.config.settings import settings

log = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.notifications = []

    def send_email(self, to, subject, body):
        if not settings.SMTP_ENABLED:
            log.info("smtp.disabled to=%s", to)
            return False
        if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASS):
            log.warning("smtp.not_configured to=%s", to)
            return False
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASS)
                message = f"Subject: {subject}\n\n{body}"
                server.sendmail(settings.SMTP_USER, to, message)
            log.info("email.sent to=%s", to)
            return True
        except smtplib.SMTPException:
            log.exception("smtp.error to=%s", to)
            return False

    def notify_task_assigned(self, user, task):
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\n"
            f"Status: {task.status}"
        )
        self.send_email(user.email, f"Nova task atribuída: {task.title}", body)
        self.notifications.append(
            {
                "type": "task_assigned",
                "user_id": user.id,
                "task_id": task.id,
                "timestamp": datetime.now(timezone.utc),
            }
        )

    def notify_task_overdue(self, user, task):
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' está atrasada!\n\n"
            f"Data limite: {task.due_date}"
        )
        self.send_email(user.email, f"Task atrasada: {task.title}", body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n["user_id"] == user_id]
