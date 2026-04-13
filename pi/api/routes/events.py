"""
SENTINEL PHANTOM - API Routes: Events
GET  /api/events          → listar eventos (filtros: session_id, module, limit, offset)
GET  /api/events/<id>     → evento por ID
POST /api/events          → insertar evento manualmente (para tests)
GET  /api/events/stats    → conteos agrupados por módulo
"""

from flask import Blueprint, jsonify, request
from database.local_db import db
from database.models import Event
from datetime import datetime

events_bp = Blueprint("events", __name__)


@events_bp.get("/events")
def list_events():
    session_id = request.args.get("session_id")
    module     = request.args.get("module")
    limit      = min(int(request.args.get("limit", 100)), 500)
    offset     = int(request.args.get("offset", 0))

    rows = db.get_events(session_id=session_id, module=module, limit=limit, offset=offset)
    return jsonify({"count": len(rows), "offset": offset, "data": rows})


@events_bp.get("/events/stats")
def events_stats():
    """Conteo de eventos agrupados por módulo (últimas 24h)."""
    rows = db._execute(
        """SELECT module, COUNT(*) as total
           FROM events
           WHERE timestamp >= datetime('now', '-24 hours')
           GROUP BY module
           ORDER BY total DESC"""
    ).fetchall()
    return jsonify({"data": [dict(r) for r in rows]})


@events_bp.get("/events/<int:event_id>")
def get_event(event_id: int):
    row = db._execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))


@events_bp.post("/events")
def create_event():
    body = request.get_json(force=True) or {}
    required = {"session_id", "module", "event_type"}
    if missing := required - body.keys():
        return jsonify({"error": f"Faltan campos: {missing}"}), 400

    import json
    event = Event(
        session_id = body["session_id"],
        module     = body["module"],
        event_type = body["event_type"],
        payload    = json.dumps(body.get("payload")) if body.get("payload") else None,
    )
    eid = db.insert_event(event)
    return jsonify({"id": eid, "status": "created"}), 201