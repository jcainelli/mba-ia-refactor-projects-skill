from flask import Blueprint, jsonify
from src.config.settings import settings

index_bp = Blueprint("index", __name__)


@index_bp.get("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": settings.VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        }
    })
