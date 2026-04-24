"""
SENTINEL PHANTOM - WIFI Evil Twin Module

Integra el ataque Evil Twin con el sistema principal y el OLED.
Sigue la misma arquitectura que RFIDModule.
"""

import asyncio
import time

from core.base_module import BaseModule
from core.logger import get_logger
from core.event_bus import bus

from hardware.pico_bridge import PicoBridge
from database.local_db import LocalDB

from modules.wifi.evil_twin import EvilTwinModule


log = get_logger("module.wifi.evil_twin")


class EvilTwinController(BaseModule):

    def __init__(self):
        super().__init__("evil_twin", enabled=True)

        self.pico = None
        self.db = None
        self.evil = None

        self._running_event = None

    # ─────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────

    async def _setup(self):

        self._running_event = asyncio.Event()

        try:
            self.pico = PicoBridge()
            self.db = LocalDB()

            self.evil = EvilTwinModule(
                pico=self.pico,
                bus=bus,
                db=self.db
            )

            log.info("Evil Twin listo ✓")

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "Evil Twin listo"}
            )

        except Exception as e:

            log.error(f"Evil Twin init error: {e}")

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "Error Evil Twin"}
            )

    # ─────────────────────────────────────────
    # LOOP
    # ─────────────────────────────────────────

    async def _run(self):

        while not self._stop_event.is_set():

            if self._running_event.is_set():

                status = self.evil.get_status()

                msg = f"Clientes: {status['count']}"

                bus.publish_sync(
                    "oled:wifi_status",
                    {"msg": msg}
                )

                await asyncio.sleep(2)

                continue

            await asyncio.sleep(0.2)

    # ─────────────────────────────────────────
    # TEARDOWN
    # ─────────────────────────────────────────

    async def _teardown(self):

        try:

            if self.evil and self.evil.running:

                self.evil.stop()

            log.info("Evil Twin detenido")

        except Exception as e:

            log.error(f"Evil Twin teardown error: {e}")

    # ─────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────

    async def start_evil_twin(
        self,
        ssid: str,
        channel: int = 6,
        password: str = ""
    ):

        log.info("start_evil_twin() iniciado")

        self._running_event.set()

        bus.publish_sync(
            "oled:wifi_status",
            {"msg": f"AP: {ssid}"}
        )

        await asyncio.sleep(1)

        try:

            loop = asyncio.get_event_loop()

            result = await loop.run_in_executor(
                None,
                self.evil.start,
                ssid,
                channel,
                password
            )

            if result:

                log.info("Evil Twin iniciado")

                bus.publish_sync(
                    "oled:wifi_status",
                    {"msg": "Evil Twin activo"}
                )

            else:

                bus.publish_sync(
                    "oled:wifi_status",
                    {"msg": "Fallo inicio"}
                )

            return result

        except Exception as e:

            log.error(f"Evil Twin start error: {e}")

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "Error Evil Twin"}
            )

            return False

    async def stop_evil_twin(self):

        log.info("stop_evil_twin()")

        try:

            loop = asyncio.get_event_loop()

            await loop.run_in_executor(
                None,
                self.evil.stop
            )

            self._running_event.clear()

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "Evil Twin detenido"}
            )

            await asyncio.sleep(1)

        except Exception as e:

            log.error(f"Evil Twin stop error: {e}")

        finally:

            bus.publish_sync(
                "oled:return_menu",
                {}
            )