# pi/api/app.py
import logging
import sys
import os

# Agregar el directorio pi/ al path para importar core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from core.config import config
from core.event_bus import EventBus, EVENTS

logger = logging.getLogger(__name__)

# ── Inicializar Flask ─────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "centinel-phantom-2025"

CORS(app, origins="*")

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet",
    logger=False,
    engineio_logger=False
)

# ── Registrar rutas ───────────────────────────────────────────────────────────
from api.routes.events  import events_bp
from api.routes.alerts  import alerts_bp
from api.routes.modules import modules_bp
from api.routes.devices import devices_bp

app.register_blueprint(events_bp,  url_prefix="/api")
app.register_blueprint(alerts_bp,  url_prefix="/api")
app.register_blueprint(modules_bp, url_prefix="/api")
app.register_blueprint(devices_bp, url_prefix="/api")

# ── WebSocket — suscribirse a eventos del bus ─────────────────────────────────
def setup_websocket_bridge():
    """
    Conecta el EventBus con SocketIO.
    Cuando un módulo publica un evento, se emite automáticamente al dashboard.
    """
    bus = EventBus.get_instance()

    def forward_to_dashboard(event: str, data: dict):
        """Reenviar cualquier evento del bus al dashboard via WebSocket"""
        parts = event.split(".")
        severity = data.get("severity", "info")

        # Emitir al canal general
        socketio.emit("event", {
            "type":     event,
            "module":   parts[0] if parts else "system",
            "data":     data,
            "severity": severity
        })

        # Emitir al canal de alertas si es warning o critical
        if severity in ("warning", "critical"):
            socketio.emit("alert", {
                "type":    event,
                "message": data.get("message", event),
                "data":    data
            })

    # Suscribirse a todos los eventos
    for event in EVENTS:
        bus.subscribe(event, forward_to_dashboard)

    logger.info("WebSocket bridge configurado")

# ── Eventos de conexión SocketIO ──────────────────────────────────────────────
@socketio.on("connect")
def on_connect():
    logger.info("Dashboard conectado")
    socketio.emit("system", {"message": "Centinel Phantom conectado", "status": "ok"})

@socketio.on("disconnect")
def on_disconnect():
    logger.info("Dashboard desconectado")

@socketio.on("ping")
def on_ping():
    socketio.emit("pong", {"status": "alive"})

# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return {"status": "ok", "system": "Centinel Phantom", "version": "1.0.0"}

# ── Arrancar ──────────────────────────────────────────────────────────────────
def start_api(modules_ref: dict = {}):
    """
    Arrancar la API Flask.
    modules_ref es una referencia a los módulos activos del sistema.
    """
    # Guardar referencia a módulos para control desde el dashboard
    app.config["MODULES"] = modules_ref

    setup_websocket_bridge()

    logger.info(f"API iniciando en puerto {config.FLASK_PORT}")
    socketio.run(
        app,
        host="0.0.0.0",
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
        use_reloader=False
    )

if __name__ == "__main__":
    start_api()