"""
SENTINEL PHANTOM - WIFI Detector Module

Integra WiFiDetector con:
- OLED display
- Event bus
- BaseModule lifecycle
- Async runtime

Detecta:
- Evil Twin
- Deauth
- Beacon flood
- Channel hop
- Security downgrade
"""

import asyncio

from core.base_module import BaseModule
from core.logger import get_logger
from core.event_bus import bus



log = get_logger("module.wifi.detector")


class WiFiDetectorModule(BaseModule):

    def __init__(self):
        super().__init__("wifi_detector", enabled=True)

        self.detector = None
        self._running_event = None

    # ─────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────

    async def _setup(self):

        self._running_event = asyncio.Event()

        try:

            self.detector = WiFiDetector(
                interface="wlan1"
            )

            # Suscribirse a alertas
            bus.subscribe(
                "wifi.alert",
                self._on_alert
            )

            log.info("WiFi Detector listo ✓")

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "Detector listo"}
            )

        except Exception as e:

            log.error(f"Detector init error: {e}")

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "Error Detector"}
            )

    # ─────────────────────────────────────────
    # LOOP
    # ─────────────────────────────────────────

    async def _run(self):

        while not self._stop_event.is_set():

            if self._running_event.is_set():

                bus.publish_sync(
                    "oled:wifi_status",
                    {"msg": "Escaneando WiFi"}
                )

                await asyncio.sleep(3)

                continue

            await asyncio.sleep(0.2)

    # ─────────────────────────────────────────
    # TEARDOWN
    # ─────────────────────────────────────────

    async def _teardown(self):

        try:

            if self.detector and self.detector.running:

                self.detector.stop()

            log.info("WiFi Detector detenido")

        except Exception as e:

            log.error(f"Detector teardown error: {e}")

    # ─────────────────────────────────────────
    # ALERT HANDLER
    # ─────────────────────────────────────────

    def _on_alert(self, event):

        try:

            alert_type = event.get("type", "unknown")

            log.warning(f"ALERTA: {alert_type}")

            msg = "Alerta WiFi"

            if alert_type == "evil_twin_detected":
                msg = "Evil Twin"

            elif alert_type == "deauth_detected":
                msg = "Deauth"

            elif alert_type == "beacon_flood_detected":
                msg = "Beacon flood"

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": msg}
            )

        except Exception as e:

            log.error(f"Alert handler error: {e}")

    # ─────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────

    async def start_detector(self):

        log.info("start_detector()")

        self._running_event.set()

        bus.publish_sync(
            "oled:wifi_status",
            {"msg": "Iniciando detector"}
        )

        await asyncio.sleep(1)

        try:

            loop = asyncio.get_event_loop()

            await loop.run_in_executor(
                None,
                self.detector.start
            )

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "Detector activo"}
            )

            return True

        except Exception as e:

            log.error(f"Detector start error: {e}")

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "Error detector"}
            )

            return False

    async def stop_detector(self):

        log.info("stop_detector()")

        try:

            loop = asyncio.get_event_loop()

            await loop.run_in_executor(
                None,
                self.detector.stop
            )

            self._running_event.clear()

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "Detector detenido"}
            )

            await asyncio.sleep(1)

        except Exception as e:

            log.error(f"Detector stop error: {e}")

        finally:

            bus.publish_sync(
                "oled:return_menu",
                {}
            )