"""
SENTINEL PHANTOM - API Flask + SocketIO
Servidor REST + WebSocket que corre en la Pi.
El Dashboard React se conecta aquí para recibir eventos en tiempo real.
"""

import json
from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from api.routes.rfid import rfid_bp
app.register_blueprint(rfid_bp, url_prefix="/api")
from config import API_HOST, API_PORT, API_DEBUG, SECRET_KEY
from core.logger import get_logger
from core.event_bus import bus
from database.local_db import db

from api.routes.events  import events_bp
from api.routes.alerts  import alerts_bp
from api.routes.modules import modules_bp
from api.routes.devices import devices_bp

log = get_logger("api.app")


def create_app(module_registry: dict | None = None) -> tuple[Flask, SocketIO]:
    """
    Factory de la app Flask.
    module_registry: dict {name: BaseModule} inyectado desde main.py
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["MODULE_REGISTRY"] = module_registry or {}

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode="threading",
        logger=False,
        engineio_logger=False,
    )

    # ── Blueprints ────────────────────────────────────────────────────────────
    prefix = "/api"
    app.register_blueprint(events_bp,  url_prefix=prefix)
    app.register_blueprint(alerts_bp,  url_prefix=prefix)
    app.register_blueprint(modules_bp, url_prefix=prefix)
    app.register_blueprint(devices_bp, url_prefix=prefix)

    # ── Health / status ───────────────────────────────────────────────────────
    @app.get("/api/health")
    def health():
        from config import DEVICE_ID, DEVICE_NAME
        stats = db.quick_stats()
        registry = app.config.get("MODULE_REGISTRY", {})
        return jsonify({
            "status":    "ok",
            "device_id": DEVICE_ID,
            "device":    DEVICE_NAME,
            "modules":   {n: m.status.value for n, m in registry.items()},
            "db_stats":  stats,
        })

    @app.get("/api/session/current")
    def current_session():
        sessions = db.get_active_sessions()
        return jsonify(sessions[0] if sessions else {})

    # ── Error handlers ────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint no encontrado"}), 404

    @app.errorhandler(500)
    def internal(e):
        return jsonify({"error": "Error interno del servidor"}), 500

    # ── SocketIO: reenvío de eventos del bus → Dashboard ──────────────────────
    def _forward_to_ws(event: dict) -> None:
        """Handler wildcard: todo lo que publica el bus llega al Dashboard via WS."""
        topic   = event.get("topic", "unknown")
        payload = event.get("payload", {})
        try:
            socketio.emit("phantom_event", {"topic": topic, "payload": payload})
        except Exception as exc:
            log.debug(f"WS emit error: {exc}")

    bus.subscribe("*", _forward_to_ws)

    @socketio.on("connect")
    def on_connect():
        log.info("Dashboard conectado via WebSocket")
        socketio.emit("phantom_event", {
            "topic": "system.connected",
            "payload": {"message": "SENTINEL PHANTOM online"}
        })

    @socketio.on("disconnect")
    def on_disconnect():
        log.info("Dashboard desconectado")

    log.info(f"Flask app creada — API en http://{API_HOST}:{API_PORT}/api")
    return app, socketio


def run_api(module_registry: dict | None = None) -> None:
    """Inicia el servidor Flask+SocketIO (bloqueante, llamar en thread)."""
    app, socketio = create_app(module_registry)
    socketio.run(app, host=API_HOST, port=API_PORT, debug=API_DEBUG, use_reloader=False)
