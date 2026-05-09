import sqlite3
from flask import Blueprint, jsonify, request

from src.config.database import get_db
from src.config.settings import settings

admin_bp = Blueprint("admin", __name__)


def _require_admin():
    if not settings.ADMIN_TOKEN:
        return jsonify({
            "erro": "Endpoints admin desabilitados (defina ADMIN_TOKEN no .env)",
            "sucesso": False,
        }), 503
    if request.headers.get("X-Admin-Token", "") != settings.ADMIN_TOKEN:
        return jsonify({"erro": "Token admin inválido", "sucesso": False}), 401
    return None


@admin_bp.post("/admin/reset-db")
def reset_database():
    auth_error = _require_admin()
    if auth_error is not None:
        return auth_error
    db = get_db()
    db.execute("DELETE FROM itens_pedido")
    db.execute("DELETE FROM pedidos")
    db.execute("DELETE FROM produtos")
    db.execute("DELETE FROM usuarios")
    db.commit()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@admin_bp.post("/admin/query")
def executar_query():
    auth_error = _require_admin()
    if auth_error is not None:
        return auth_error
    data = request.get_json(silent=True) or {}
    query = (data.get("sql") or "").strip()
    if not query:
        return jsonify({"erro": "Query não informada", "sucesso": False}), 400
    if not query.upper().startswith("SELECT"):
        return jsonify({"erro": "Apenas SELECT é permitido", "sucesso": False}), 400
    conn = sqlite3.connect(f"file:{settings.DATABASE_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(query).fetchall()
        return jsonify({"dados": [dict(r) for r in rows], "sucesso": True}), 200
    finally:
        conn.close()
