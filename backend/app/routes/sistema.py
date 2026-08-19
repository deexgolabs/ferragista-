from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db

sistema_bp = Blueprint("sistema", __name__)


@sistema_bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        status_banco = "ok"
    except Exception:
        status_banco = "indisponivel"
    return jsonify({"status": "ok" if status_banco == "ok" else "instabilidade", "banco": status_banco})
