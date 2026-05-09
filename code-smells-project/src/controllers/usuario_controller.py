from src.middlewares.error_handler import NotFoundError, ValidationError
from src.models import usuario_model


def list_usuarios():
    return usuario_model.get_todos()


def get_usuario(usuario_id):
    usuario = usuario_model.get_por_id(usuario_id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar_usuario(data):
    if not data:
        raise ValidationError("Dados inválidos")
    nome = (data.get("nome") or "").strip()
    email = (data.get("email") or "").strip()
    senha = data.get("senha") or ""
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if len(senha) < 4:
        raise ValidationError("Senha muito curta")
    return usuario_model.criar(nome, email, senha)
