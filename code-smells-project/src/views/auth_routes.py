from flask import Blueprint, jsonify, request

from src.controllers import auth_controller

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True)
    usuario = auth_controller.login(data)
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
