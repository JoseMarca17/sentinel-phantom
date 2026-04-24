from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from core.logger import get_logger
from core.event_bus import bus
from database.local_db import insert_event, insert_alert # Importar funciones de DB [cite: 37, 38]

# Importar rutas
from api.routes.alerts import alerts_bp
from api.routes.devices import devices_bp
from api.routes.events import events_bp
from api.routes.modules import modules_bp
from api.routes.rfid import rfid_bp

log = get_logger("api")

# Configurar SocketIO para que el frontend pueda escuchar [cite: 131, 132]
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

# --- Puente entre Event Bus y Socket.io --- [cite: 133, 134]
def setup_event_bridge():
    """Escucha el bus interno y lo retransmite al Dashboard y a la DB."""
    
    @bus.on("wifi:event")
    @bus.on("bt:event")
    @bus.on("rfid:event")
    def handle_module_events(payload):
        # 1. Persistencia en base de datos [cite: 1, 2]
        try:
            insert_event(payload) 
        except Exception as e:
            log.error(f"Error guardando evento en DB: {e}")

        # 2. Retransmitir al Dashboard en tiempo real [cite: 323, 324]
        socketio.emit("dashboard:update", {"new_event": payload})
        log.info(f"📡 Evento enviado al Dashboard: {payload.get('type')}")

    @bus.on("wifi.alert")
    def handle_alerts(payload):
        # 1. Guardar alerta en DB [cite: 37, 38]
        insert_alert(payload)
        # 2. Notificar al Dashboard específicamente para el contador de alertas 
        socketio.emit("alert:new", payload)

def create_app(module_registry=None):
    app = Flask(__name__)
    CORS(app)

    # Guardar módulos en el contexto de la app para que las rutas los usen [cite: 271, 272]
    app.config["MODULE_REGISTRY"] = module_registry or {}

    # Registrar blueprints
    app.register_blueprint(alerts_bp, url_prefix="/api")
    app.register_blueprint(devices_bp, url_prefix="/api")
    app.register_blueprint(events_bp, url_prefix="/api")
    app.register_blueprint(modules_bp, url_prefix="/api")
    app.register_blueprint(rfid_bp, url_prefix="/api")

    return app

def run_api(module_registry=None):
    app = create_app(module_registry)
    socketio.init_app(app)

    # Iniciar el puente de eventos antes de correr el servidor
    setup_event_bridge()

    log.info("🚀 SENTINEL PHANTOM API corriendo en http://0.0.0.0:5000")

    # Importante: usar socketio.run en lugar de app.run para WebSocket [cite: 131, 132]
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False # Evita doble ejecución del bridge
    )