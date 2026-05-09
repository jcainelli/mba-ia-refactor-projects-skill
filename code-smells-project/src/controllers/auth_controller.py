from src.middlewares.error_handler import UnauthorizedError, ValidationError
from src.models import usuario_model


def login(data):
    if not data:
        raise ValidationError("Dados inválidos")
    email = (data.get("email") or "").strip()
    senha = data.get("senha") or ""
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    row = usuario_model.get_por_email_full(email)
    if row is None or not usuario_model.check_password(senha, row["password_hash"]):
        raise UnauthorizedError("Email ou senha inválidos")
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
    }
