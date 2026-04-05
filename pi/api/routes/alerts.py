# pi/api/routes/alerts.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sqlite3
from flask import Blueprint, request, jsonify
from core.config import config
from core.logger import CentinelLogger

alerts_bp = Blueprint("alerts", __name__)
db = CentinelLogger()

@alerts_bp.route("/alerts", methods=["GET"])
def get_alerts():
    """GET /api/alerts — alertas activas sin resolver"""
    resolved = request.args.get("resolved", "false") == "true"
    alerts = db.get_alerts(resolved=resolved)
    return jsonify({
        "status": "ok",
        "count":  len(alerts),
        "alerts": alerts
    })

@alerts_bp.route("/alerts/<int:alert_id>/resolve", methods=["POST"])
def resolve_alert(alert_id):
    """POST /api/alerts/:id/resolve — marcar alerta como resuelta"""
    with sqlite3.connect(config.DB_LOCAL_PATH) as conn:
        conn.execute(
            "UPDATE alerts SET resolved = 1 WHERE id = ?",
            (alert_id,)
        )
    return jsonify({"status": "ok", "message": f"Alerta {alert_id} resuelta"})

@alerts_bp.route("/alerts/resolve-all", methods=["POST"])
def resolve_all():
    """POST /api/alerts/resolve-all — limpiar todas las alertas"""
    with sqlite3.connect(config.DB_LOCAL_PATH) as conn:
        conn.execute("UPDATE alerts SET resolved = 1 WHERE resolved = 0")
    return jsonify({"status": "ok", "message": "Todas las alertas resueltas"})

@alerts_bp.route("/alerts/count", methods=["GET"])
def count_alerts():
    """GET /api/alerts/count — cantidad de alertas activas para el badge"""
    with sqlite3.connect(config.DB_LOCAL_PATH) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE resolved = 0"
        ).fetchone()[0]
    return jsonify({"status": "ok", "count": count})