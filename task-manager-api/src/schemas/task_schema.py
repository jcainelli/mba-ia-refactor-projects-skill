from marshmallow import EXCLUDE, Schema, fields, validate

from src.config.constants import (
    DEFAULT_PRIORITY,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    VALID_TASK_STATUSES,
)


class TaskCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.String(
        required=True,
        validate=validate.Length(
            min=MIN_TITLE_LENGTH,
            max=MAX_TITLE_LENGTH,
            error=f"Título deve ter entre {MIN_TITLE_LENGTH} e {MAX_TITLE_LENGTH} caracteres",
        ),
    )
    description = fields.String(load_default="")
    status = fields.String(
        load_default="pending",
        validate=validate.OneOf(VALID_TASK_STATUSES, error="Status inválido"),
    )
    priority = fields.Integer(
        load_default=DEFAULT_PRIORITY,
        strict=True,
        validate=validate.Range(
            min=MIN_PRIORITY,
            max=MAX_PRIORITY,
            error=f"Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}",
        ),
    )
    user_id = fields.Integer(load_default=None, allow_none=True)
    category_id = fields.Integer(load_default=None, allow_none=True)
    due_date = fields.String(load_default=None, allow_none=True)
    tags = fields.Raw(load_default=None, allow_none=True)


class TaskUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.String(
        validate=validate.Length(
            min=MIN_TITLE_LENGTH,
            max=MAX_TITLE_LENGTH,
            error=f"Título deve ter entre {MIN_TITLE_LENGTH} e {MAX_TITLE_LENGTH} caracteres",
        )
    )
    description = fields.String()
    status = fields.String(
        validate=validate.OneOf(VALID_TASK_STATUSES, error="Status inválido")
    )
    priority = fields.Integer(
        strict=True,
        validate=validate.Range(
            min=MIN_PRIORITY,
            max=MAX_PRIORITY,
            error=f"Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}",
        ),
    )
    user_id = fields.Integer(allow_none=True)
    category_id = fields.Integer(allow_none=True)
    due_date = fields.String(allow_none=True)
    tags = fields.Raw()
