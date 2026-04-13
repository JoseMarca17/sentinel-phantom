"""
SENTINEL PHANTOM — Server API: Export
Exporta datos en CSV o JSON para análisis forense offline.

GET /api/export/alerts?format=csv&session_id=...
GET /api/export/events?format=json&module=wifi
GET /api/export/devices?format=csv
GET /api/export/report/<session_id>    → reporte completo JSON de sesión
"""

import csv
import io
import json
from datetime import datetime

from flask import Blueprint, Response, jsonify, request
from database.db import fetchall, fetchone

export_bp = Blueprint("export", __name__)


def _to_csv(rows: list[dict], filename: str) -> Response:
    if not rows:
        return Response("", mimetype="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _to_json(data: dict | list, filename: str) -> Response:
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _ts() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


# ── Alertas ───────────────────────────────────────────────────────────────────

@export_bp.get("/export/alerts")
def export_alerts():
    fmt        = request.args.get("format", "csv").lower()
    session_id = request.args.get("session_id")
    severity   = request.args.get("severity")

    sql    = "SELECT * FROM alerts WHERE 1=1"
    params: list = []
    if session_id:
        sql += " AND session_id=?"; params.append(session_id)
    if severity:
        sql += " AND severity=?";   params.append(severity)
    sql += " ORDER BY timestamp DESC"

    rows = fetchall(sql, tuple(params))
    fn   = f"phantom_alerts_{_ts()}"

    return _to_csv(rows, f"{fn}.csv") if fmt == "csv" else _to_json(rows, f"{fn}.json")


# ── Eventos ───────────────────────────────────────────────────────────────────

@export_bp.get("/export/events")
def export_events():
    fmt        = request.args.get("format", "csv").lower()
    session_id = request.args.get("session_id")
    module     = request.args.get("module")

    sql    = "SELECT * FROM events WHERE 1=1"
    params: list = []
    if session_id:
        sql += " AND session_id=?"; params.append(session_id)
    if module:
        sql += " AND module=?";     params.append(module)
    sql += " ORDER BY timestamp DESC"

    rows = fetchall(sql, tuple(params))
    fn   = f"phantom_events_{_ts()}"

    return _to_csv(rows, f"{fn}.csv") if fmt == "csv" else _to_json(rows, f"{fn}.json")


# ── Dispositivos ──────────────────────────────────────────────────────────────

@export_bp.get("/export/devices")
def export_devices():
    fmt        = request.args.get("format", "csv").lower()
    session_id = request.args.get("session_id")

    sql    = "SELECT * FROM devices WHERE 1=1"
    params: list = []
    if session_id:
        sql += " AND session_id=?"; params.append(session_id)
    sql += " ORDER BY last_seen DESC"

    rows = fetchall(sql, tuple(params))
    fn   = f"phantom_devices_{_ts()}"

    return _to_csv(rows, f"{fn}.csv") if fmt == "csv" else _to_json(rows, f"{fn}.json")


# ── Reporte completo de sesión ────────────────────────────────────────────────

@export_bp.get("/export/report/<session_id>")
def export_session_report(session_id: str):
    session = fetchone("SELECT * FROM sessions WHERE id=?", (session_id,))
    if not session:
        return jsonify({"error": "Sesión no encontrada"}), 404

    events  = fetchall("SELECT * FROM events  WHERE session_id=? ORDER BY timestamp", (session_id,))
    alerts  = fetchall("SELECT * FROM alerts  WHERE session_id=? ORDER BY timestamp", (session_id,))
    devices = fetchall("SELECT * FROM devices WHERE session_id=? ORDER BY first_seen", (session_id,))

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "session": session,
        "summary": {
            "total_events":   len(events),
            "total_alerts":   len(alerts),
            "total_devices":  len(devices),
            "critical_alerts": sum(1 for a in alerts if a.get("severity") in ("HIGH", "CRITICAL")),
        },
        "events":  events,
        "alerts":  alerts,
        "devices": devices,
    }

    fn = f"phantom_report_{session_id[:8]}_{_ts()}.json"
    return _to_json(report, fn)