"""
pi/modules/wifi/evil_twin.py
Coordinador del ataque Evil Twin desde la Pi 3B.

Usa el Pico W como AP y opcionalmente lanza un portal cautivo
en la Pi para capturar credenciales (para demostración en lab).
"""

import logging
import threading
import time
from typing import Optional
from hardware.pico_bridge import PicoBridge
from core.event_bus import EventBus
from database.local_db import LocalDB

logger = logging.getLogger(__name__)


class EvilTwinModule:
    """
    Coordina el Evil Twin:
      1. Envía comando start al Pico W con el SSID objetivo
      2. Escucha eventos de clientes conectados
      3. Registra todo en la base de datos local
      4. Publica alertas en el event bus
    """

    def __init__(self, pico: PicoBridge, bus: EventBus, db: LocalDB):
        self.pico    = pico
        self.bus     = bus
        self.db      = db
        self.running = False
        self.ssid    = None
        self.clients: list[dict] = []

        # Registrar handlers de eventos del Pico W
        self.pico.on_event("ap_up",       self._on_ap_up)
        self.pico.on_event("ap_down",     self._on_ap_down)
        self.pico.on_event("client_join", self._on_client_join)
        self.pico.on_event("client_leave",self._on_client_leave)

    # ── Arranque ─────────────────────────────────────────────────
    def start(self, ssid: str, channel: int = 6, password: str = ""):
        """
        Levanta el Evil Twin con el SSID dado.
        Uso desde el menú OLED o desde la API Flask.
        """
        if self.running:
            logger.warning("Evil Twin ya está activo")
            return False

        self.ssid    = ssid
        self.clients = []
        self.running = True

        logger.info(f"[EvilTwin] Iniciando AP '{ssid}' canal {channel}")
        return self.pico.send_command("start", {
            "ssid":     ssid,
            "channel":  channel,
            "password": password,
        })

    def stop(self):
        """Detiene el Evil Twin."""
        if not self.running:
            return
        self.pico.send_command("stop")
        self.running = False
        self.clients = []
        logger.info("[EvilTwin] AP detenido")

    def get_status(self) -> dict:
        return {
            "running": self.running,
            "ssid":    self.ssid,
            "clients": self.clients,
            "count":   len(self.clients),
        }

    # ── Handlers de eventos del Pico W ───────────────────────────
    def _on_ap_up(self, event, module, data):
        logger.info(f"[EvilTwin] AP activo: SSID='{data['ssid']}' "
                    f"IP={data['ip']} abierto={data['open']}")
        self.db.insert_event(
            module="wifi",
            type="evil_twin_ap_up",
            severity="high",
            data=data,
        )
        self.bus.publish("alert:new", {
            "level":   "high",
            "module":  "wifi",
            "message": f"Evil Twin activo: '{data['ssid']}' en {data['ip']}",
        })

    def _on_ap_down(self, event, module, data):
        logger.info("[EvilTwin] AP detenido")
        self.bus.publish("module:status", {
            "module": "evil_twin",
            "status": "idle",
        })

    def _on_client_join(self, event, module, data):
        mac   = data["mac"]
        total = data["total"]
        logger.warning(f"[EvilTwin] Cliente conectado: {mac} "
                       f"(total={total})")
        self.clients.append({"mac": mac, "connected_at": time.time()})

        self.db.insert_event(
            module="wifi",
            type="evil_twin_client",
            severity="critical",
            data={"mac": mac, "ssid": self.ssid, "total": total},
        )
        self.bus.publish("alert:new", {
            "level":   "critical",
            "module":  "wifi",
            "message": f"Cliente conectado al Evil Twin: {mac}",
        })

    def _on_client_leave(self, event, module, data):
        mac = data["mac"]
        logger.info(f"[EvilTwin] Cliente desconectado: {mac}")
        self.clients = [c for c in self.clients if c["mac"] != mac]
