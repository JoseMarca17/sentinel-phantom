"""
SENTINEL PHANTOM - API Routes: Alerts
GET  /api/alerts                  → listar alertas (filtros opcionales)
GET  /api/alerts/<id>             → alerta por ID
POST /api/alerts/<id>/acknowledge → marcar como reconocida
GET  /api/alerts/summary          → resumen por severidad
"""

from flask import Blueprint, jsonify, request
from database.local_db import db

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.get("/alerts")
def list_alerts():
    session_id   = request.args.get("session_id")
    severity     = request.args.get("severity")
    acknowledged = request.args.get("acknowledged")  # "true"/"false"
    limit        = min(int(request.args.get("limit", 100)), 500)
    offset       = int(request.args.get("offset", 0))

    ack_filter = None
    if acknowledged is not None:
        ack_filter = acknowledged.lower() == "true"

    rows = db.get_alerts(
        session_id=session_id,
        severity=severity,
        acknowledged=ack_filter,
        limit=limit,
        offset=offset,
    )
    return jsonify({"count": len(rows), "offset": offset, "data": rows})


@alerts_bp.get("/alerts/summary")
def alerts_summary():
    """Conteo agrupado por severidad."""
    rows = db._execute(
        """SELECT severity, COUNT(*) as total, SUM(acknowledged) as acked
           FROM alerts
           GROUP BY severity
           ORDER BY CASE severity
               WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3
               WHEN 'LOW' THEN 4 ELSE 5 END"""
    ).fetchall()
    return jsonify({"data": [dict(r) for r in rows]})


@alerts_bp.get("/alerts/<int:alert_id>")
def get_alert(alert_id: int):
    row = db._execute("SELECT * FROM alerts WHERE id=?", (alert_id,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))


@alerts_bp.post("/alerts/<int:alert_id>/acknowledge")
def acknowledge_alert(alert_id: int):
    ok = db.acknowledge_alert(alert_id)
    if not ok:
        return jsonify({"error": "Alert not found"}), 404
    return jsonify({"id": alert_id, "status": "acknowledged"})