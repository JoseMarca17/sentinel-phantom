"""
modules/wifi/engine.py

Motor principal del WiFi IDS.
Orquesta los módulos:

- detector
- attacker
- evil twin
- pmkid
"""

import asyncio

from core.logger import get_logger

from modules.wifi.detector import WifiDetector
from modules.wifi.attacker import WifiAttacker
from modules.wifi.evil_twin import EvilTwin
from modules.wifi.pmkid import PmkidAttack

log = get_logger("wifi.engine")


class WifiIDS:

    def __init__(self):

        self.running = False

        # módulos internos
        self.detector = WifiDetector()
        self.attacker = WifiAttacker()
        self.evil_twin = EvilTwin()
        self.pmkid = PmkidAttack()

    async def start(self):

        if self.running:
            log.warning("WifiIDS ya está corriendo")
            return

        self.running = True

        log.info("=== WIFI IDS ENGINE START ===")

        try:

            # ejemplo básico: iniciar detector
            await self.detector.start()

            while self.running:

                await asyncio.sleep(1)

        except Exception as e:

            log.error(f"Error en WifiIDS engine: {e}")

        finally:

            log.info("WifiIDS engine detenido")

    async def stop(self):

        if not self.running:
            return

        log.info("Deteniendo WifiIDS engine")

        self.running = False

        try:

            await self.detector.stop()

        except Exception as e:

            log.error(f"Error al detener detector: {e}")