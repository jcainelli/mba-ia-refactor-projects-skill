from src.config.constants import PEDIDO_STATUS_VALIDOS
from src.middlewares.error_handler import ValidationError
from src.models import pedido_model
from src.services.notification_service import notify_pedido_criado, notify_pedido_status


def listar_todos():
    return pedido_model.get_todos_com_itens()


def listar_por_usuario(usuario_id):
    return pedido_model.get_por_usuario(usuario_id)


def criar_pedido(data):
    if not data:
        raise ValidationError("Dados inválidos")
    usuario_id = data.get("usuario_id")
    itens = data.get("itens") or []
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not isinstance(itens, list) or not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    normalized = []
    for raw in itens:
        try:
            normalized.append({
                "produto_id": int(raw["produto_id"]),
                "quantidade": int(raw["quantidade"]),
            })
        except (KeyError, TypeError, ValueError):
            raise ValidationError(
                "Item inválido — produto_id e quantidade são obrigatórios e numéricos"
            )

    try:
        result = pedido_model.criar_com_itens(int(usuario_id), normalized)
    except ValueError as exc:
        raise ValidationError(str(exc))

    notify_pedido_criado(usuario_id=int(usuario_id), pedido_id=result["pedido_id"])
    return result


def atualizar_status(pedido_id, data):
    novo_status = (data or {}).get("status", "")
    if novo_status not in PEDIDO_STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    pedido_model.atualizar_status(pedido_id, novo_status)
    notify_pedido_status(pedido_id=pedido_id, status=novo_status)
