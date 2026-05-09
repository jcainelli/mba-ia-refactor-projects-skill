from flask import Blueprint, jsonify, request

from src.controllers import produto_controller
from src.middlewares.error_handler import ValidationError

produto_bp = Blueprint("produto", __name__)


@produto_bp.get("/produtos")
def listar_produtos():
    return jsonify({"dados": produto_controller.list_produtos(), "sucesso": True}), 200


@produto_bp.get("/produtos/busca")
def buscar_produtos():
    args = request.args
    termo = args.get("q") or None
    categoria = args.get("categoria") or None
    try:
        preco_min = float(args["preco_min"]) if args.get("preco_min") else None
        preco_max = float(args["preco_max"]) if args.get("preco_max") else None
    except ValueError:
        raise ValidationError("preco_min/preco_max devem ser numéricos")
    resultados = produto_controller.buscar_produtos(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


@produto_bp.get("/produtos/<int:produto_id>")
def buscar_produto(produto_id):
    return jsonify({"dados": produto_controller.get_produto(produto_id), "sucesso": True}), 200


@produto_bp.post("/produtos")
def criar_produto():
    data = request.get_json(silent=True)
    novo_id = produto_controller.criar_produto(data)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


@produto_bp.put("/produtos/<int:produto_id>")
def atualizar_produto(produto_id):
    data = request.get_json(silent=True)
    produto_controller.atualizar_produto(produto_id, data)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@produto_bp.delete("/produtos/<int:produto_id>")
def deletar_produto(produto_id):
    produto_controller.deletar_produto(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
