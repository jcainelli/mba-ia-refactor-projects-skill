from flask import Blueprint, jsonify, request

from src.controllers import usuario_controller

usuario_bp = Blueprint("usuario", __name__)


@usuario_bp.get("/usuarios")
def listar():
    return jsonify({"dados": usuario_controller.list_usuarios(), "sucesso": True}), 200


@usuario_bp.get("/usuarios/<int:usuario_id>")
def buscar(usuario_id):
    return jsonify({"dados": usuario_controller.get_usuario(usuario_id), "sucesso": True}), 200


@usuario_bp.post("/usuarios")
def criar():
    data = request.get_json(silent=True)
    novo_id = usuario_controller.criar_usuario(data)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201
