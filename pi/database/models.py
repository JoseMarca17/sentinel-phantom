"""
SENTINEL PHANTOM - Modelos de base de datos (SQLite local en Pi)
Define el esquema y los dataclasses que mapean cada tabla.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ─── SQL DDL ─────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ── Sesiones de auditoría ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    device_id   TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    notes       TEXT,
    synced      INTEGER DEFAULT 0
);

-- ── Dispositivos detectados ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS devices (
    id            TEXT PRIMARY KEY,
    session_id    TEXT REFERENCES sessions(id),
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL,
    device_type   TEXT NOT NULL,   -- wifi | bluetooth | rfid | drone | ir
    mac           TEXT,
    vendor        TEXT,
    ssid          TEXT,
    signal_dbm    INTEGER,
    extra         TEXT,            -- JSON con campos adicionales por módulo
    threat_level  TEXT DEFAULT 'INFO',
    synced        INTEGER DEFAULT 0
);

-- ── Eventos (log táctico) ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT REFERENCES sessions(id),
    timestamp   TEXT NOT NULL,
    module      TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    payload     TEXT,              -- JSON
    synced      INTEGER DEFAULT 0
);

-- ── Alertas de seguridad ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT REFERENCES sessions(id),
    timestamp    TEXT NOT NULL,
    module       TEXT NOT NULL,
    alert_type   TEXT NOT NULL,
    severity     TEXT NOT NULL,    -- INFO | LOW | MEDIUM | HIGH | CRITICAL
    description  TEXT NOT NULL,
    device_mac   TEXT,
    extra        TEXT,             -- JSON
    acknowledged INTEGER DEFAULT 0,
    synced       INTEGER DEFAULT 0
);

-- ── Índices ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_events_session   ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_module    ON events(module);
CREATE INDEX IF NOT EXISTS idx_alerts_severity  ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_session   ON alerts(session_id);
CREATE INDEX IF NOT EXISTS idx_devices_session  ON devices(session_id);
CREATE INDEX IF NOT EXISTS idx_devices_mac      ON devices(mac);
"""


# ─── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class Session:
    id:         str
    device_id:  str
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ended_at:   Optional[str] = None
    notes:      Optional[str] = None
    synced:     int = 0


@dataclass
class Device:
    id:           str
    session_id:   str
    first_seen:   str
    last_seen:    str
    device_type:  str
    mac:          Optional[str] = None
    vendor:       Optional[str] = None
    ssid:         Optional[str] = None
    signal_dbm:   Optional[int] = None
    extra:        Optional[str] = None   # JSON string
    threat_level: str = "INFO"
    synced:       int = 0


@dataclass
class Event:
    session_id:  str
    module:      str
    event_type:  str
    payload:     Optional[str] = None    # JSON string
    timestamp:   str = field(default_factory=lambda: datetime.utcnow().isoformat())
    id:          Optional[int] = None
    synced:      int = 0


@dataclass
class Alert:
    session_id:   str
    module:       str
    alert_type:   str
    severity:     str
    description:  str
    device_mac:   Optional[str] = None
    extra:        Optional[str] = None   # JSON string
    timestamp:    str = field(default_factory=lambda: datetime.utcnow().isoformat())
    id:           Optional[int] = None
    acknowledged: int = 0
    synced:       int = 0