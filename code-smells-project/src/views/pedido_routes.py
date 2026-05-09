from flask import Blueprint, jsonify, request

from src.controllers import pedido_controller

pedido_bp = Blueprint("pedido", __name__)


@pedido_bp.post("/pedidos")
def criar():
    data = request.get_json(silent=True)
    result = pedido_controller.criar_pedido(data)
    return jsonify({"dados": result, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@pedido_bp.get("/pedidos")
def listar_todos():
    return jsonify({"dados": pedido_controller.listar_todos(), "sucesso": True}), 200


@pedido_bp.get("/pedidos/usuario/<int:usuario_id>")
def listar_por_usuario(usuario_id):
    return jsonify({"dados": pedido_controller.listar_por_usuario(usuario_id), "sucesso": True}), 200


@pedido_bp.put("/pedidos/<int:pedido_id>/status")
def atualizar_status(pedido_id):
    data = request.get_json(silent=True)
    pedido_controller.atualizar_status(pedido_id, data)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
