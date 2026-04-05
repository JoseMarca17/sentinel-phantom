# pi/api/routes/modules.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request, jsonify, current_app

modules_bp = Blueprint("modules", __name__)

@modules_bp.route("/modules/status", methods=["GET"])
def get_status():
    """GET /api/modules/status — estado de todos los módulos"""
    modules = current_app.config.get("MODULES", {})

    status = {}
    for name, module in modules.items():
        try:
            status[name] = module.status()
        except Exception as e:
            status[name] = {"running": False, "error": str(e)}

    # Si no hay módulos reales, retornar mock para desarrollo
    if not status:
        status = {
            "wifi":      {"running": False, "interface": "wlan1"},
            "bluetooth": {"running": False},
            "rfid":      {"running": False},
            "tscm":      {"running": False},
            "nrf24":     {"running": False},
        }

    return jsonify({"status": "ok", "modules": status})

@modules_bp.route("/modules/<module_name>/start", methods=["POST"])
def start_module(module_name):
    """POST /api/modules/:name/start — arrancar un módulo"""
    modules = current_app.config.get("MODULES", {})

    if module_name not in modules:
        return jsonify({
            "status": "error",
            "message": f"Modulo '{module_name}' no encontrado"
        }), 404

    try:
        modules[module_name].start()
        return jsonify({
            "status":  "ok",
            "message": f"Modulo {module_name} iniciado"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@modules_bp.route("/modules/<module_name>/stop", methods=["POST"])
def stop_module(module_name):
    """POST /api/modules/:name/stop — detener un módulo"""
    modules = current_app.config.get("MODULES", {})

    if module_name not in modules:
        return jsonify({
            "status": "error",
            "message": f"Modulo '{module_name}' no encontrado"
        }), 404

    try:
        modules[module_name].stop()
        return jsonify({
            "status":  "ok",
            "message": f"Modulo {module_name} detenido"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500