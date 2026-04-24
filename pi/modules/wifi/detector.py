from core.logger import get_logger
from core.event_bus import bus
import threading
import time
import random

log = get_logger("wifi.detector")


class WifiDetector:
    def __init__(self, interface="wlan1"):
        self.interface = interface
        self.running = False
        self._thread = None

    def start(self):
        if self.running:
            log.warning("Detector ya estaba corriendo")
            return

        self.running = True
        log.info(f"Detector iniciado en {self.interface}")

        self._thread = threading.Thread(
            target=self._loop,
            daemon=True
        )
        self._thread.start()

    def _loop(self):
        """
        Loop fake de detección (simulación).
        Luego aquí puedes meter scapy o airodump.
        """

        fake_networks = [
            "MOVISTAR_1234",
            "TP-LINK_ABCD",
            "NETGEAR_XYZ",
            "HACKME_WIFI",
            "STARLINK"
        ]

        while self.running:

            ssid = random.choice(fake_networks)
            power = random.randint(-90, -30)

            msg = f"{ssid[:8]} {power}dBm"

            # 🔥 enviar a OLED
            bus.publish_sync(
                "oled:wifi_status",
                {"msg": msg}
            )

            log.info(f"Detectado: {ssid} ({power} dBm)")

            time.sleep(2)

    def stop(self):
        self.running = False
        log.info("Detector detenido")

        bus.publish_sync(
            "oled:wifi_status",
            {"msg": "Detector OFF"}
        )