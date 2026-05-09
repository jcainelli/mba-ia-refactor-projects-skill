from marshmallow import ValidationError as MarshmallowValidationError

from src.middlewares.error_handler import BadRequestError


def _first_error(messages):
    if isinstance(messages, dict):
        for value in messages.values():
            result = _first_error(value)
            if result:
                return result
        return None
    if isinstance(messages, list):
        for item in messages:
            result = _first_error(item)
            if result:
                return result
        return None
    return messages


def load_or_400(schema, payload):
    try:
        return schema.load(payload or {})
    except MarshmallowValidationError as exc:
        raise BadRequestError(_first_error(exc.messages) or "Dados inválidos")
