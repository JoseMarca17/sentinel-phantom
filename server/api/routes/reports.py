"""
SENTINEL PHANTOM — Server API: Reports
Consulta las vistas SQL Server para generar reportes forenses.

GET /api/reports/daily-summary          → actividad por día y módulo
GET /api/reports/top-threats            → top 50 amenazas últimas 24h
GET /api/reports/session-devices        → resumen de dispositivos por sesión
GET /api/reports/critical-timeline      → timeline de alertas HIGH/CRITICAL
GET /api/reports/module-stats           → estadísticas por módulo
"""

from flask import Blueprint, jsonify, request
from database.db import fetchall, fetchone

reports_bp = Blueprint("reports", __name__)


@reports_bp.get("/reports/daily-summary")
def daily_summary():
    """Actividad agrupada por fecha y módulo."""
    days   = int(request.args.get("days", 7))
    module = request.args.get("module")

    sql = """
        SELECT fecha, module, total_eventos, sesiones_activas
        FROM vw_daily_summary
        WHERE fecha >= CAST(DATEADD(DAY, ?, GETUTCDATE()) AS DATE)
    """
    params: list = [-days]

    if module:
        sql += " AND module = ?"
        params.append(module)

    sql += " ORDER BY fecha DESC, total_eventos DESC"
    rows = fetchall(sql, tuple(params))
    return jsonify({"period_days": days, "count": len(rows), "data": rows})


@reports_bp.get("/reports/top-threats")
def top_threats():
    """Top amenazas detectadas en las últimas 24h."""
    rows = fetchall("SELECT * FROM vw_top_threats")
    return jsonify({"count": len(rows), "data": rows})


@reports_bp.get("/reports/session-devices")
def session_devices():
    """Resumen de dispositivos y alertas por sesión."""
    limit  = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))

    rows = fetchall(
        """SELECT * FROM vw_session_devices
           ORDER BY started_at DESC
           OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
        (offset, limit),
    )
    return jsonify({"count": len(rows), "offset": offset, "data": rows})


@reports_bp.get("/reports/critical-timeline")
def critical_timeline():
    """Timeline de alertas HIGH y CRITICAL."""
    limit      = min(int(request.args.get("limit", 100)), 500)
    session_id = request.args.get("session_id")

    sql    = "SELECT TOP (?) * FROM vw_critical_timeline"
    params: list = [limit]

    if session_id:
        sql += " WHERE session_id = ?"
        params.append(session_id)

    sql += " ORDER BY timestamp DESC"
    rows = fetchall(sql, tuple(params))
    return jsonify({"count": len(rows), "data": rows})


@reports_bp.get("/reports/module-stats")
def module_stats():
    """Estadísticas globales por módulo."""
    rows = fetchall("SELECT * FROM vw_module_stats ORDER BY total_eventos DESC")
    return jsonify({"count": len(rows), "data": rows})


@reports_bp.get("/reports/overview")
def overview():
    """Resumen ejecutivo rápido para el Dashboard."""
    total_sessions = fetchone("SELECT COUNT(*) AS n FROM sessions")
    total_devices  = fetchone("SELECT COUNT(*) AS n FROM devices")
    total_alerts   = fetchone("SELECT COUNT(*) AS n FROM alerts")
    critical       = fetchone(
        "SELECT COUNT(*) AS n FROM alerts WHERE severity IN ('HIGH','CRITICAL')"
    )
    top_module     = fetchone(
        "SELECT TOP 1 module, COUNT(*) AS n FROM events GROUP BY module ORDER BY n DESC"
    )
    return jsonify({
        "total_sessions": total_sessions["n"] if total_sessions else 0,
        "total_devices":  total_devices["n"]  if total_devices  else 0,
        "total_alerts":   total_alerts["n"]   if total_alerts   else 0,
        "critical_alerts":critical["n"]        if critical       else 0,
        "top_module":     top_module["module"] if top_module     else None,
    })