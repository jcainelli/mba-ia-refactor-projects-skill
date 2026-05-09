from flask import Blueprint, jsonify
from src.config.settings import settings

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    return jsonify({"status": "ok", "version": settings.VERSION}), 200
