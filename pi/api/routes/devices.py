# pi/api/routes/devices.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sqlite3
from flask import Blueprint, request, jsonify
from core.config import config

devices_bp = Blueprint("devices", __name__)

@devices_bp.route("/devices", methods=["GET"])
def get_devices():
    """GET /api/devices — todos los dispositivos detectados"""
    module = request.args.get("module", None)

    query  = "SELECT * FROM devices"
    params = []

    if module:
        query += " WHERE module = ?"
        params.append(module)

    query += " ORDER BY last_seen DESC"

    with sqlite3.connect(config.DB_LOCAL_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    return jsonify({
        "status":  "ok",
        "count":   len(rows),
        "devices": [dict(r) for r in rows]
    })

@devices_bp.route("/devices/<mac>/whitelist", methods=["POST"])
def whitelist_device(mac):
    """POST /api/devices/:mac/whitelist — agregar dispositivo a whitelist"""
    mac = mac.replace("-", ":").lower()

    with sqlite3.connect(config.DB_LOCAL_PATH) as conn:
        conn.execute(
            "UPDATE devices SET is_whitelisted = 1 WHERE mac_address = ?",
            (mac,)
        )

    return jsonify({
        "status":  "ok",
        "message": f"Dispositivo {mac} agregado a whitelist"
    })

@devices_bp.route("/devices/<mac>/whitelist", methods=["DELETE"])
def remove_whitelist(mac):
    """DELETE /api/devices/:mac/whitelist — quitar de whitelist"""
    mac = mac.replace("-", ":").lower()

    with sqlite3.connect(config.DB_LOCAL_PATH) as conn:
        conn.execute(
            "UPDATE devices SET is_whitelisted = 0 WHERE mac_address = ?",
            (mac,)
        )

    return jsonify({
        "status":  "ok",
        "message": f"Dispositivo {mac} removido de whitelist"
    })

@devices_bp.route("/devices/stats", methods=["GET"])
def get_stats():
    """GET /api/devices/stats — estadísticas para el dashboard"""
    with sqlite3.connect(config.DB_LOCAL_PATH) as conn:
        total     = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
        by_module = conn.execute("""
            SELECT module, COUNT(*) as count
            FROM devices GROUP BY module
        """).fetchall()
        unknown   = conn.execute("""
            SELECT COUNT(*) FROM devices WHERE is_whitelisted = 0
        """).fetchone()[0]

    return jsonify({
        "status": "ok",
        "stats": {
            "total":     total,
            "unknown":   unknown,
            "by_module": [{"module": r[0], "count": r[1]} for r in by_module]
        }
    })