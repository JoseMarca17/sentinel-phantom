"""
SENTINEL PHANTOM - API Routes: Devices
GET  /api/devices               → listar dispositivos detectados
GET  /api/devices/<id>          → dispositivo por ID
GET  /api/devices/stats         → conteo por tipo y threat_level
"""

from flask import Blueprint, jsonify, request
from database.local_db import db

devices_bp = Blueprint("devices", __name__)


@devices_bp.get("/devices")
def list_devices():
    session_id  = request.args.get("session_id")
    device_type = request.args.get("type")
    limit       = min(int(request.args.get("limit", 200)), 1000)
    offset      = int(request.args.get("offset", 0))

    rows = db.get_devices(
        session_id=session_id,
        device_type=device_type,
        limit=limit,
        offset=offset,
    )
    return jsonify({"count": len(rows), "offset": offset, "data": rows})


@devices_bp.get("/devices/stats")
def devices_stats():
    rows_type = db._execute(
        "SELECT device_type, COUNT(*) as total FROM devices GROUP BY device_type"
    ).fetchall()
    rows_threat = db._execute(
        "SELECT threat_level, COUNT(*) as total FROM devices GROUP BY threat_level"
    ).fetchall()
    return jsonify({
        "by_type":         [dict(r) for r in rows_type],
        "by_threat_level": [dict(r) for r in rows_threat],
    })


@devices_bp.get("/devices/<device_id>")
def get_device(device_id: str):
    row = db._execute("SELECT * FROM devices WHERE id=?", (device_id,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))