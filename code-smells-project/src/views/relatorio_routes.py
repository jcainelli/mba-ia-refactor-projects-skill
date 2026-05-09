from flask import Blueprint, jsonify

from src.services.relatorio_service import gerar_relatorio_vendas

relatorio_bp = Blueprint("relatorio", __name__)


@relatorio_bp.get("/relatorios/vendas")
def relatorio_vendas():
    return jsonify({"dados": gerar_relatorio_vendas(), "sucesso": True}), 200
