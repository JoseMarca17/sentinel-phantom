# pi/api/routes/events.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request, jsonify
from core.logger import CentinelLogger

events_bp = Blueprint("events", __name__)
db = CentinelLogger()

@events_bp.route("/events", methods=["GET"])
def get_events():
    """
    GET /api/events
    Params:
        limit  = cantidad de eventos (default 50)
        module = filtrar por módulo (wifi, bluetooth, rfid...)
        severity = filtrar por severidad (info, warning, critical)
    """
    limit    = request.args.get("limit",    50,   type=int)
    module   = request.args.get("module",   None, type=str)
    severity = request.args.get("severity", None, type=str)

    events = db.get_recent_events(limit=limit, module=module)

    # Filtrar por severidad si se especifica
    if severity:
        events = [e for e in events if e.get("severity") == severity]

    return jsonify({
        "status": "ok",
        "count":  len(events),
        "events": events
    })

@events_bp.route("/events/summary", methods=["GET"])
def get_summary():
    """
    GET /api/events/summary
    Resumen de eventos por módulo para el dashboard
    """
    import sqlite3
    from core.config import config

    with sqlite3.connect(config.DB_LOCAL_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT
                module,
                COUNT(*) as total,
                COUNT(CASE WHEN severity='critical' THEN 1 END) as critical,
                COUNT(CASE WHEN severity='warning'  THEN 1 END) as warning,
                COUNT(CASE WHEN severity='info'     THEN 1 END) as info,
                MAX(timestamp) as last_event
            FROM events
            GROUP BY module
        """).fetchall()

    return jsonify({
        "status":  "ok",
        "summary": [dict(r) for r in rows]
    })

@events_bp.route("/events/recent", methods=["GET"])
def get_recent():
    """GET /api/events/recent — últimos 10 eventos para el widget del dashboard"""
    events = db.get_recent_events(limit=10)
    return jsonify({"status": "ok", "events": events})