"""
SENTINEL PHANTOM — Server API: History
Consulta histórica de sesiones, eventos, alertas y dispositivos.

GET /api/history/sessions             → todas las sesiones
GET /api/history/sessions/<id>        → sesión con detalle completo
GET /api/history/events               → eventos (filtros)
GET /api/history/alerts               → alertas (filtros)
GET /api/history/devices              → dispositivos (filtros)
GET /api/history/search               → búsqueda por MAC o SSID
"""

from flask import Blueprint, jsonify, request
from database.db import fetchall, fetchone

history_bp = Blueprint("history", __name__)


# ── Sesiones ──────────────────────────────────────────────────────────────────

@history_bp.get("/history/sessions")
def list_sessions():
    limit  = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))

    rows = fetchall(
        """SELECT * FROM sessions
           ORDER BY started_at DESC
           OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
        (offset, limit),
    )
    return jsonify({"count": len(rows), "offset": offset, "data": rows})


@history_bp.get("/history/sessions/<session_id>")
def session_detail(session_id: str):
    session = fetchone("SELECT * FROM sessions WHERE id=?", (session_id,))
    if not session:
        return jsonify({"error": "Sesión no encontrada"}), 404

    events  = fetchall("SELECT * FROM events  WHERE session_id=? ORDER BY timestamp DESC", (session_id,))
    alerts  = fetchall("SELECT * FROM alerts  WHERE session_id=? ORDER BY timestamp DESC", (session_id,))
    devices = fetchall("SELECT * FROM devices WHERE session_id=? ORDER BY last_seen  DESC", (session_id,))

    return jsonify({
        "session": session,
        "events":  {"count": len(events),  "data": events},
        "alerts":  {"count": len(alerts),  "data": alerts},
        "devices": {"count": len(devices), "data": devices},
    })


# ── Eventos ───────────────────────────────────────────────────────────────────

@history_bp.get("/history/events")
def list_events():
    session_id = request.args.get("session_id")
    module     = request.args.get("module")
    limit      = min(int(request.args.get("limit", 100)), 500)
    offset     = int(request.args.get("offset", 0))

    sql    = "SELECT * FROM events WHERE 1=1"
    params: list = []

    if session_id:
        sql += " AND session_id=?"
        params.append(session_id)
    if module:
        sql += " AND module=?"
        params.append(module)

    sql += " ORDER BY timestamp DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
    params += [offset, limit]

    rows = fetchall(sql, tuple(params))
    return jsonify({"count": len(rows), "offset": offset, "data": rows})


# ── Alertas ───────────────────────────────────────────────────────────────────

@history_bp.get("/history/alerts")
def list_alerts():
    session_id = request.args.get("session_id")
    severity   = request.args.get("severity")
    module     = request.args.get("module")
    limit      = min(int(request.args.get("limit", 100)), 500)
    offset     = int(request.args.get("offset", 0))

    sql    = "SELECT * FROM alerts WHERE 1=1"
    params: list = []

    if session_id:
        sql += " AND session_id=?"
        params.append(session_id)
    if severity:
        sql += " AND severity=?"
        params.append(severity)
    if module:
        sql += " AND module=?"
        params.append(module)

    sql += " ORDER BY timestamp DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
    params += [offset, limit]

    rows = fetchall(sql, tuple(params))
    return jsonify({"count": len(rows), "offset": offset, "data": rows})


# ── Dispositivos ──────────────────────────────────────────────────────────────

@history_bp.get("/history/devices")
def list_devices():
    session_id  = request.args.get("session_id")
    device_type = request.args.get("type")
    threat      = request.args.get("threat_level")
    limit       = min(int(request.args.get("limit", 200)), 1000)
    offset      = int(request.args.get("offset", 0))

    sql    = "SELECT * FROM devices WHERE 1=1"
    params: list = []

    if session_id:
        sql += " AND session_id=?"
        params.append(session_id)
    if device_type:
        sql += " AND device_type=?"
        params.append(device_type)
    if threat:
        sql += " AND threat_level=?"
        params.append(threat)

    sql += " ORDER BY last_seen DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
    params += [offset, limit]

    rows = fetchall(sql, tuple(params))
    return jsonify({"count": len(rows), "offset": offset, "data": rows})


# ── Búsqueda global ───────────────────────────────────────────────────────────

@history_bp.get("/history/search")
def search():
    """Busca dispositivos y alertas por MAC o SSID."""
    q = request.args.get("q", "").strip()
    if len(q) < 3:
        return jsonify({"error": "Búsqueda mínima de 3 caracteres"}), 400

    pattern = f"%{q}%"

    devices = fetchall(
        """SELECT TOP 50 * FROM devices
           WHERE mac LIKE ? OR ssid LIKE ? OR vendor LIKE ?
           ORDER BY last_seen DESC""",
        (pattern, pattern, pattern),
    )
    alerts = fetchall(
        """SELECT TOP 50 * FROM alerts
           WHERE device_mac LIKE ? OR description LIKE ?
           ORDER BY timestamp DESC""",
        (pattern, pattern),
    )

    return jsonify({
        "query":   q,
        "devices": {"count": len(devices), "data": devices},
        "alerts":  {"count": len(alerts),  "data": alerts},
    })