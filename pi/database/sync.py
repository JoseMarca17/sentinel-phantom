"""
SENTINEL PHANTOM - Sincronización Pi → Servidor Central
Envía en batch los registros no sincronizados al servidor Flask
que corre en la laptop del equipo. Funciona en background thread.
"""

import asyncio
import threading
import time
from typing import Optional

import requests

from config import DEVICE_ID, SERVER_API_KEY, SERVER_URL, SYNC_INTERVAL_S
from core.logger import get_logger
from database.local_db import db

log = get_logger("database.sync")


class SyncManager:
    """
    Sincroniza datos locales (SQLite) al servidor central (SQL Server via Flask).
    Corre en un thread daemon independiente.
    """

    def __init__(self) -> None:
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "X-API-Key": SERVER_API_KEY,
            "X-Device-ID": DEVICE_ID,
        })
        self._server = SERVER_URL.rstrip("/")
        self._success_count = 0
        self._fail_count = 0

    # ── Control ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="sync-manager")
        self._thread.start()
        log.info(f"SyncManager iniciado (intervalo: {SYNC_INTERVAL_S}s → {self._server})")

    def stop(self) -> None:
        self._running = False
        log.info("SyncManager detenido")

    # ── Loop principal ───────────────────────────────────────────────────────

    def _loop(self) -> None:
        while self._running:
            try:
                self._sync_cycle()
            except Exception as exc:
                self._fail_count += 1
                log.error(f"Error en ciclo de sync: {exc}")
            time.sleep(SYNC_INTERVAL_S)

    def _sync_cycle(self) -> None:
        synced_any = False

        # ── Events
        events = db.get_unsynced_events(batch=100)
        if events:
            ok = self._push("/sync/events", events)
            if ok:
                db.mark_events_synced([e["id"] for e in events])
                synced_any = True
                log.debug(f"Sincronizados {len(events)} events")

        # ── Alerts
        alerts = db.get_unsynced_alerts(batch=100)
        if alerts:
            ok = self._push("/sync/alerts", alerts)
            if ok:
                db.mark_alerts_synced([a["id"] for a in alerts])
                synced_any = True
                log.debug(f"Sincronizadas {len(alerts)} alerts")

        # ── Devices
        devices = db.get_unsynced_devices(batch=100)
        if devices:
            ok = self._push("/sync/devices", devices)
            if ok:
                db.mark_devices_synced([d["id"] for d in devices])
                synced_any = True
                log.debug(f"Sincronizados {len(devices)} devices")

        if synced_any:
            self._success_count += 1

    def _push(self, endpoint: str, records: list[dict]) -> bool:
        url = f"{self._server}{endpoint}"
        try:
            resp = self._session.post(url, json={"records": records}, timeout=10)
            if resp.status_code == 200:
                return True
            log.warning(f"Sync {endpoint} → HTTP {resp.status_code}: {resp.text[:120]}")
            return False
        except requests.exceptions.ConnectionError:
            log.debug(f"Servidor no disponible ({url}) — se reintentará")
            return False
        except requests.exceptions.Timeout:
            log.warning(f"Timeout al sincronizar {endpoint}")
            return False
        except Exception as exc:
            log.error(f"Error inesperado en sync {endpoint}: {exc}")
            return False

    # ── Sync manual (on-demand) ───────────────────────────────────────────────

    def force_sync(self) -> dict:
        """Dispara una sincronización inmediata (puede llamarse desde la API)."""
        log.info("Sync manual solicitado")
        try:
            self._sync_cycle()
            return {"status": "ok", "success_cycles": self._success_count}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    def status(self) -> dict:
        return {
            "running":         self._running,
            "server":          self._server,
            "sync_interval_s": SYNC_INTERVAL_S,
            "success_cycles":  self._success_count,
            "fail_cycles":     self._fail_count,
        }


# Instancia global
sync_manager = SyncManager()