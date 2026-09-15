from flask import Blueprint, jsonify
from sqlalchemy import text

from ..extensions import db

health_bp = Blueprint("health", __name__, url_prefix="/api/health")


@health_bp.get("")
def health_check():
    return jsonify({"status": "ok", "service": "carebridge-api"})


@health_bp.get("/ready")
def readiness_check():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db.session.rollback()
        return jsonify({"status": "not_ready", "service": "carebridge-api", "database": "unavailable"}), 503

    return jsonify({"status": "ready", "service": "carebridge-api", "database": "ok"}), 200
