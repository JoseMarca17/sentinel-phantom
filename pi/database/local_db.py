"""
SENTINEL PHANTOM - Base de Datos Local (SQLite)
CRUD completo para events, alerts, devices y sessions.
Thread-safe mediante check_same_thread=False + lock propio.
"""

import json
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Optional

from config import DB_PATH
from core.logger import get_logger
from database.models import SCHEMA_SQL, Alert, Device, Event, Session

log = get_logger("database.local")


class LocalDB:
    """Interfaz SQLite thread-safe para Sentinel Phantom."""

    _instance: "LocalDB | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "LocalDB":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._db_lock = threading.Lock()
        self._apply_schema()
        log.info(f"SQLite abierto en {DB_PATH}")

    def _apply_schema(self) -> None:
        with self._db_lock:
            self._conn.executescript(SCHEMA_SQL)
            self._conn.commit()

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._db_lock:
            return self._conn.execute(sql, params)

    def _executemany(self, sql: str, data: list[tuple]) -> None:
        with self._db_lock:
            self._conn.executemany(sql, data)
            self._conn.commit()

    def _commit_execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._db_lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return cur

    # ── Sessions ─────────────────────────────────────────────────────────────

    def create_session(self, session: Session) -> Session:
        self._commit_execute(
            "INSERT INTO sessions (id, device_id, started_at, ended_at, notes, synced) VALUES (?,?,?,?,?,?)",
            (session.id, session.device_id, session.started_at, session.ended_at, session.notes, session.synced),
        )
        log.info(f"Sesión creada: {session.id}")
        return session

    def close_session(self, session_id: str, notes: Optional[str] = None) -> None:
        self._commit_execute(
            "UPDATE sessions SET ended_at=?, notes=COALESCE(?, notes) WHERE id=?",
            (datetime.utcnow().isoformat(), notes, session_id),
        )
        log.info(f"Sesión cerrada: {session_id}")

    def get_session(self, session_id: str) -> Optional[dict]:
        row = self._execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        return dict(row) if row else None

    def get_active_sessions(self) -> list[dict]:
        rows = self._execute("SELECT * FROM sessions WHERE ended_at IS NULL ORDER BY started_at DESC").fetchall()
        return [dict(r) for r in rows]

    # ── Events ───────────────────────────────────────────────────────────────

    def insert_event(self, event: Event) -> int:
        cur = self._commit_execute(
            "INSERT INTO events (session_id, timestamp, module, event_type, payload, synced) VALUES (?,?,?,?,?,?)",
            (event.session_id, event.timestamp, event.module, event.event_type, event.payload, event.synced),
        )
        return cur.lastrowid  # type: ignore

    def get_events(
        self,
        session_id: Optional[str] = None,
        module: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        sql = "SELECT * FROM events WHERE 1=1"
        params: list[Any] = []
        if session_id:
            sql += " AND session_id=?"
            params.append(session_id)
        if module:
            sql += " AND module=?"
            params.append(module)
        sql += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = self._execute(sql, tuple(params)).fetchall()
        return [dict(r) for r in rows]

    def get_unsynced_events(self, batch: int = 50) -> list[dict]:
        rows = self._execute(
            "SELECT * FROM events WHERE synced=0 ORDER BY id ASC LIMIT ?", (batch,)
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_events_synced(self, ids: list[int]) -> None:
        if not ids:
            return
        placeholders = ",".join("?" * len(ids))
        self._commit_execute(f"UPDATE events SET synced=1 WHERE id IN ({placeholders})", tuple(ids))

    # ── Alerts ───────────────────────────────────────────────────────────────

    def insert_alert(self, alert: Alert) -> int:
        cur = self._commit_execute(
            """INSERT INTO alerts
               (session_id, timestamp, module, alert_type, severity, description, device_mac, extra, synced)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                alert.session_id, alert.timestamp, alert.module,
                alert.alert_type, alert.severity, alert.description,
                alert.device_mac, alert.extra, alert.synced,
            ),
        )
        log.warning(f"[ALERT] [{alert.severity}] {alert.module} — {alert.description}")
        return cur.lastrowid  # type: ignore

    def get_alerts(
        self,
        session_id: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        sql = "SELECT * FROM alerts WHERE 1=1"
        params: list[Any] = []
        if session_id:
            sql += " AND session_id=?"
            params.append(session_id)
        if severity:
            sql += " AND severity=?"
            params.append(severity)
        if acknowledged is not None:
            sql += " AND acknowledged=?"
            params.append(1 if acknowledged else 0)
        sql += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = self._execute(sql, tuple(params)).fetchall()
        return [dict(r) for r in rows]

    def acknowledge_alert(self, alert_id: int) -> bool:
        cur = self._commit_execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,))
        return cur.rowcount > 0  # type: ignore

    def get_unsynced_alerts(self, batch: int = 50) -> list[dict]:
        rows = self._execute(
            "SELECT * FROM alerts WHERE synced=0 ORDER BY id ASC LIMIT ?", (batch,)
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_alerts_synced(self, ids: list[int]) -> None:
        if not ids:
            return
        placeholders = ",".join("?" * len(ids))
        self._commit_execute(f"UPDATE alerts SET synced=1 WHERE id IN ({placeholders})", tuple(ids))

    # ── Devices ──────────────────────────────────────────────────────────────

    def upsert_device(self, device: Device) -> Device:
        """Inserta o actualiza (por MAC + session) un dispositivo detectado."""
        self._commit_execute(
            """INSERT INTO devices
               (id, session_id, first_seen, last_seen, device_type, mac, vendor, ssid, signal_dbm, extra, threat_level, synced)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                   last_seen=excluded.last_seen,
                   signal_dbm=excluded.signal_dbm,
                   extra=excluded.extra,
                   threat_level=excluded.threat_level,
                   synced=0""",
            (
                device.id, device.session_id, device.first_seen, device.last_seen,
                device.device_type, device.mac, device.vendor, device.ssid,
                device.signal_dbm, device.extra, device.threat_level, device.synced,
            ),
        )
        return device

    def get_devices(
        self,
        session_id: Optional[str] = None,
        device_type: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[dict]:
        sql = "SELECT * FROM devices WHERE 1=1"
        params: list[Any] = []
        if session_id:
            sql += " AND session_id=?"
            params.append(session_id)
        if device_type:
            sql += " AND device_type=?"
            params.append(device_type)
        sql += " ORDER BY last_seen DESC LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = self._execute(sql, tuple(params)).fetchall()
        return [dict(r) for r in rows]

    def get_unsynced_devices(self, batch: int = 50) -> list[dict]:
        rows = self._execute(
            "SELECT * FROM devices WHERE synced=0 ORDER BY first_seen ASC LIMIT ?", (batch,)
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_devices_synced(self, ids: list[str]) -> None:
        if not ids:
            return
        placeholders = ",".join("?" * len(ids))
        self._commit_execute(f"UPDATE devices SET synced=1 WHERE id IN ({placeholders})", tuple(ids))

    # ── Stats rápidas ────────────────────────────────────────────────────────

    def quick_stats(self, session_id: Optional[str] = None) -> dict:
        filter_sql = "WHERE session_id=?" if session_id else ""
        params = (session_id,) if session_id else ()

        total_events  = self._execute(f"SELECT COUNT(*) FROM events {filter_sql}", params).fetchone()[0]
        total_alerts  = self._execute(f"SELECT COUNT(*) FROM alerts {filter_sql}", params).fetchone()[0]
        total_devices = self._execute(f"SELECT COUNT(*) FROM devices {filter_sql}", params).fetchone()[0]
        critical      = self._execute(
            f"SELECT COUNT(*) FROM alerts {filter_sql} {'AND' if filter_sql else 'WHERE'} severity IN ('HIGH','CRITICAL')",
            params,
        ).fetchone()[0]

        return {
            "total_events":   total_events,
            "total_alerts":   total_alerts,
            "total_devices":  total_devices,
            "critical_alerts": critical,
        }

    def close(self) -> None:
        self._conn.close()
        log.info("Conexión SQLite cerrada")


# Instancia global
db = LocalDB()