# pi/core/logger.py
import sqlite3
import logging
import json
import threading
from datetime import datetime
from pathlib import Path
from core.config import config
from core.event_bus import EventBus, EVENTS

# Configurar logging del sistema
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

class CentinelLogger:
    """
    Logger centralizado — guarda todos los eventos en SQLite.
    Se suscribe al event_bus y registra automáticamente todo.
    """

    def __init__(self):
        self.db_path = config.DB_LOCAL_PATH
        self._lock = threading.Lock()
        self._init_db()
        self._subscribe_to_events()

    def _init_db(self):
        """Crear las tablas si no existen"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
                    module      TEXT NOT NULL,
                    event_type  TEXT NOT NULL,
                    severity    TEXT NOT NULL DEFAULT 'info',
                    source_mac  TEXT,
                    target_mac  TEXT,
                    details     TEXT,
                    synced      INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS devices (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    mac_address  TEXT UNIQUE NOT NULL,
                    first_seen   DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen    DATETIME DEFAULT CURRENT_TIMESTAMP,
                    module       TEXT NOT NULL,
                    vendor       TEXT,
                    device_name  TEXT,
                    rssi         INTEGER,
                    is_whitelisted INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id    INTEGER REFERENCES events(id),
                    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alert_type  TEXT NOT NULL,
                    message     TEXT NOT NULL,
                    resolved    INTEGER DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                    ON events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_events_module 
                    ON events(module);
                CREATE INDEX IF NOT EXISTS idx_events_severity 
                    ON events(severity);
            """)
        logger.info(f"Base de datos inicializada: {self.db_path}")

    def _subscribe_to_events(self):
        """Suscribirse a todos los eventos para registrarlos"""
        bus = EventBus.get_instance()
        for event in EVENTS:
            bus.subscribe(event, self._on_event)

    def _on_event(self, event: str, data: dict):
        """Callback — se llama cuando llega cualquier evento"""
        parts = event.split(".")
        module = parts[0] if len(parts) > 0 else "system"

        self.log_event(
            module=module,
            event_type=event,
            severity=data.get("severity", "info"),
            source_mac=data.get("source_mac"),
            target_mac=data.get("target_mac"),
            details=data
        )

    def log_event(self, module: str, event_type: str, severity: str = "info",
                  source_mac: str = None, target_mac: str = None, details: dict = {}):
        """Guardar evento en SQLite"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO events 
                            (module, event_type, severity, source_mac, target_mac, details)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (module, event_type, severity, source_mac, target_mac,
                          json.dumps(details)))
                logger.debug(f"Evento guardado: {event_type} [{severity}]")
            except Exception as e:
                logger.error(f"Error guardando evento: {e}")

    def get_recent_events(self, limit: int = 50, module: str = None) -> list:
        """Obtener eventos recientes para el dashboard"""
        query = "SELECT * FROM events"
        params = []

        if module:
            query += " WHERE module = ?"
            params.append(module)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_alerts(self, resolved: bool = False) -> list:
        """Obtener alertas activas"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM alerts WHERE resolved = ? ORDER BY timestamp DESC",
                (1 if resolved else 0,)
            ).fetchall()
            return [dict(row) for row in rows]

    def upsert_device(self, mac: str, module: str, name: str = None,
                      vendor: str = None, rssi: int = None):
        """Registrar o actualizar dispositivo detectado"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO devices (mac_address, module, device_name, vendor, rssi)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(mac_address) DO UPDATE SET
                        last_seen = CURRENT_TIMESTAMP,
                        rssi = excluded.rssi
                """, (mac, module, name, vendor, rssi))