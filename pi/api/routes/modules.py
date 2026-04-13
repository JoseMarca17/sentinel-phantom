"""
SENTINEL PHANTOM - API Routes: Modules
GET  /api/modules           → estado de todos los módulos
GET  /api/modules/<name>    → estado de un módulo
POST /api/modules/<name>/start
POST /api/modules/<name>/stop
GET  /api/modules/sync/status  → estado del SyncManager
POST /api/modules/sync/force   → forzar sincronización inmediata
"""

import asyncio
from flask import Blueprint, jsonify, current_app, request
from database.sync import sync_manager

modules_bp = Blueprint("modules", __name__)


def _get_registry():
    """Retorna el registro de módulos desde el contexto de la app."""
    return current_app.config.get("MODULE_REGISTRY", {})


@modules_bp.get("/modules")
def list_modules():
    registry = _get_registry()
    return jsonify({
        "count": len(registry),
        "modules": [m.info() for m in registry.values()]
    })


@modules_bp.get("/modules/<name>")
def get_module(name: str):
    registry = _get_registry()
    mod = registry.get(name)
    if not mod:
        return jsonify({"error": f"Módulo '{name}' no encontrado"}), 404
    return jsonify(mod.info())


@modules_bp.post("/modules/<name>/start")
def start_module(name: str):
    registry = _get_registry()
    mod = registry.get(name)
    if not mod:
        return jsonify({"error": f"Módulo '{name}' no encontrado"}), 404

    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(mod.start())
        loop.close()
        return jsonify({"module": name, "status": mod.status.value})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@modules_bp.post("/modules/<name>/stop")
def stop_module(name: str):
    registry = _get_registry()
    mod = registry.get(name)
    if not mod:
        return jsonify({"error": f"Módulo '{name}' no encontrado"}), 404

    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(mod.stop())
        loop.close()
        return jsonify({"module": name, "status": mod.status.value})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── Sync ─────────────────────────────────────────────────────────────────────

@modules_bp.get("/modules/sync/status")
def sync_status():
    return jsonify(sync_manager.status())


@modules_bp.post("/modules/sync/force")
def sync_force():
    result = sync_manager.force_sync()
    return jsonify(result)