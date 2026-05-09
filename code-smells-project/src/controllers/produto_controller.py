from src.config.constants import (
    PRODUTO_NOME_MIN, PRODUTO_NOME_MAX, CATEGORIAS_VALIDAS,
)
from src.middlewares.error_handler import NotFoundError, ValidationError
from src.models import produto_model


def list_produtos():
    return produto_model.get_todos()


def get_produto(produto_id):
    produto = produto_model.get_por_id(produto_id)
    if produto is None:
        raise NotFoundError("Produto não encontrado")
    return produto


def buscar_produtos(termo=None, categoria=None, preco_min=None, preco_max=None):
    return produto_model.buscar(termo, categoria, preco_min, preco_max)


def _validate_payload(data):
    if not data:
        raise ValidationError("Dados inválidos")

    nome = data.get("nome")
    preco = data.get("preco")
    estoque = data.get("estoque")
    if nome is None:
        raise ValidationError("Nome é obrigatório")
    if preco is None:
        raise ValidationError("Preço é obrigatório")
    if estoque is None:
        raise ValidationError("Estoque é obrigatório")

    nome = str(nome).strip()
    try:
        preco = float(preco)
        estoque = int(estoque)
    except (TypeError, ValueError):
        raise ValidationError("Preço e estoque devem ser numéricos")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if not (PRODUTO_NOME_MIN <= len(nome) <= PRODUTO_NOME_MAX):
        raise ValidationError(
            f"Nome deve ter entre {PRODUTO_NOME_MIN} e {PRODUTO_NOME_MAX} caracteres"
        )

    categoria = data.get("categoria") or "geral"
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(f"Categoria inválida. Válidas: {list(CATEGORIAS_VALIDAS)}")

    return {
        "nome": nome,
        "descricao": str(data.get("descricao") or ""),
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def criar_produto(data):
    payload = _validate_payload(data)
    return produto_model.criar(**payload)


def atualizar_produto(produto_id, data):
    if produto_model.get_por_id(produto_id) is None:
        raise NotFoundError("Produto não encontrado")
    payload = _validate_payload(data)
    produto_model.atualizar(produto_id, **payload)


def deletar_produto(produto_id):
    if produto_model.get_por_id(produto_id) is None:
        raise NotFoundError("Produto não encontrado")
    produto_model.deletar(produto_id)
