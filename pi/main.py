"""
╔══════════════════════════════════════════════════════════╗
║   SENTINEL PHANTOM — Sistema Portátil de Auditoría      ║
║   Táctica, Observación de Señales y Respuesta           ║
║   ante Amenazas                                          ║
║                                                          ║
║   Escuela Militar de Ingeniería (EMI) — Open House 2026  ║
║   Carrera: Ingeniería de Sistemas                        ║
╚══════════════════════════════════════════════════════════╝

Punto de entrada principal.
Orquesta: módulos tácticos, API Flask+SocketIO, DB local, sincronización.
"""

import asyncio
import signal
import sys
import threading
import uuid
from datetime import datetime

from config import DEVICE_ID, MODULES_ENABLED
from core.event_bus import bus as event_bus
from core.logger import get_logger
from database.local_db import db
from database.models import Event, Session
from database.sync import sync_manager

log = get_logger("main")

# ── Registro de módulos ───────────────────────────────────────────────────────
# Se importan solo los módulos habilitados para evitar errores de hardware
MODULE_REGISTRY: dict = {}


def _load_modules() -> None:
    """Importa e instancia los módulos habilitados."""
    if MODULES_ENABLED.get("wifi"):
        try:
            from modules.wifi.wifi_module import WiFiModule
            MODULE_REGISTRY["wifi"] = WiFiModule()
            log.info("Módulo WiFi cargado ✓")
        except ImportError as e:
            log.warning(f"WiFi module no disponible: {e}")

    if MODULES_ENABLED.get("bluetooth"):
        try:
            from modules.bluetooth.bt_module import BluetoothModule
            MODULE_REGISTRY["bluetooth"] = BluetoothModule()
            log.info("Módulo Bluetooth cargado ✓")
        except ImportError as e:
            log.warning(f"Bluetooth module no disponible: {e}")

    if MODULES_ENABLED.get("rfid"):
        try:
            from modules.rfid.rfid_module import RFIDModule
            MODULE_REGISTRY["rfid"] = RFIDModule()
            log.info("Módulo RFID cargado ✓")
        except ImportError as e:
            log.warning(f"RFID module no disponible: {e}")

    if MODULES_ENABLED.get("tscm"):
        try:
            from modules.tscm.tscm_module import TSCMModule
            MODULE_REGISTRY["tscm"] = TSCMModule()
            log.info("Módulo TSCM cargado ✓")
        except ImportError as e:
            log.warning(f"TSCM module no disponible: {e}")

    if MODULES_ENABLED.get("ir"):
        try:
            from modules.ir.ir_module import IRModule
            MODULE_REGISTRY["ir"] = IRModule()
            log.info("Módulo IR cargado ✓")
        except ImportError as e:
            log.warning(f"IR module no disponible: {e}")

    if MODULES_ENABLED.get("nrf24"):
        try:
            from modules.nrf24.nrf24_module import NRF24Module
            MODULE_REGISTRY["nrf24"] = NRF24Module()
            log.info("Módulo nRF24 cargado ✓")
        except ImportError as e:
            log.warning(f"nRF24 module no disponible: {e}")


# ── Sesión de auditoría ───────────────────────────────────────────────────────

def _create_session() -> str:
    session_id = str(uuid.uuid4())
    session = Session(
        id        = session_id,
        device_id = DEVICE_ID,
        started_at= datetime.utcnow().isoformat(),
        notes     = f"Sesión automática — Open House 2026",
    )
    db.create_session(session)
    log.info(f"Sesión creada: {session_id}")
    return session_id


# ── Handlers de eventos del bus ───────────────────────────────────────────────

def _setup_event_handlers(session_id: str) -> None:
    """Suscribe handlers globales que persisten eventos/alertas en SQLite."""
    import json

    def on_alert(event: dict) -> None:
        from database.models import Alert
        payload = event.get("payload", {})
        alert = Alert(
            session_id  = payload.get("session_id", session_id),
            module      = payload.get("module", "unknown"),
            alert_type  = payload.get("alert_type", "GENERIC"),
            severity    = payload.get("severity", "INFO"),
            description = payload.get("description", str(payload)),
            device_mac  = payload.get("mac"),
            extra       = json.dumps(payload.get("extra")) if payload.get("extra") else None,
        )
        db.insert_alert(alert)

    def on_event(event: dict) -> None:
        topic   = event.get("topic", "")
        payload = event.get("payload", {})
        parts   = topic.split(".", 1)
        module  = parts[0] if len(parts) >= 1 else "unknown"
        ev_type = parts[1] if len(parts) >= 2 else topic

        ev = Event(
            session_id = payload.get("session_id", session_id),
            module     = module,
            event_type = ev_type,
            payload    = json.dumps(payload),
        )
        db.insert_event(ev)

    # Alertas → topics que terminan en .alert o .threat
    for suffix in ["alert", "threat", "deauth_detected", "evil_twin_detected",
                   "drone_detected", "mousejack_detected"]:
        bus.subscribe(f"*.{suffix}", on_alert)

    # Todos los eventos → persistencia
    bus.subscribe("*", on_event)
    log.info("Event handlers registrados en el bus")


# ── API en thread separado ────────────────────────────────────────────────────

def _start_api() -> None:
    from api.app import run_api
    log.info("Iniciando API Flask + SocketIO...")
    run_api(MODULE_REGISTRY)


# ── Loop principal ────────────────────────────────────────────────────────────

async def _main_loop(session_id: str) -> None:
    """Inicia todos los módulos habilitados y espera señal de cierre."""
    log.info("Iniciando módulos tácticos...")

    for name, module in MODULE_REGISTRY.items():
        try:
            await module.start()
        except Exception as exc:
            log.error(f"No se pudo iniciar '{name}': {exc}")

    log.info("═" * 55)
    log.info("  SENTINEL PHANTOM — Sistema operativo")
    log.info(f"  Módulos activos: {[n for n, m in MODULE_REGISTRY.items() if m.status.value == 'RUNNING']}")
    log.info("═" * 55)

    # Esperar señal de cierre
    stop = asyncio.Event()

    def _handle_signal(*_):
        log.info("Señal de cierre recibida (SIGINT/SIGTERM)")
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:
            # Windows no soporta add_signal_handler en asyncio
            signal.signal(sig, _handle_signal)

    await stop.wait()

    # ── Shutdown ordenado ─────────────────────────────────────────────────────
    log.info("Apagando módulos...")
    for name, module in MODULE_REGISTRY.items():
        try:
            await module.stop()
        except Exception as exc:
            log.error(f"Error al detener '{name}': {exc}")

    db.close_session(session_id, notes="Sesión cerrada correctamente")
    sync_manager.stop()
    db.close()
    log.info("SENTINEL PHANTOM — Apagado completo. Hasta la próxima.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    log.info("╔══════════════════════════════════════════╗")
    log.info("║       SENTINEL PHANTOM — Iniciando       ║")
    log.info("╚══════════════════════════════════════════╝")

    # 1. Cargar módulos
    _load_modules()

    # 2. Crear sesión
    session_id = _create_session()

    # 3. Registrar handlers del bus
    _setup_event_handlers(session_id)

    # 4. Iniciar SyncManager en background
    sync_manager.start()

    # 5. Iniciar API en thread daemon
    api_thread = threading.Thread(target=_start_api, daemon=True, name="api-server")
    api_thread.start()

    # 6. Loop principal asyncio
    try:
        asyncio.run(_main_loop(session_id))
    except KeyboardInterrupt:
        log.info("Interrupción por teclado")
    except Exception as exc:
        log.critical(f"Error fatal: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()