from core.event_bus import bus
from core.logger import get_logger

# IMPORTS CORREGIDOS (minúsculas)
from modules.wifi.detector import WiFiDetector
from modules.wifi.attacker import WifiAttacker
from modules.wifi.pmkid import PMKIDCapture
from modules.wifi.evil_twin import EvilTwin

import threading

log = get_logger("wifi.module")


class WifiModule:

    def __init__(self, interface="wlan1"):

        self.interface = interface
        self.running = False

        # ───────── MÓDULOS ─────────

        self.detector = WiFiDetector(interface=interface)

        self.attacker = WifiAttacker(
            interface=interface
        )

        self.pmkid = PMKIDCapture(
            interface=interface
        )

        self.evil_twin = EvilTwin(
            interface="wlan0"
        )

        self._detector_thread = None

        self._attack_lock = threading.Lock()

        # ───────── EVENT BUS ─────────

        bus.subscribe(
            "oled:action",
            self._handle_oled_action
        )

        bus.subscribe(
            "wifi.alert",
            self._on_alert
        )

        log.info("WifiModule inicializado")

    # ─────────────────────────────────────
    # CICLO DE VIDA
    # ─────────────────────────────────────

    def start(self):

        if self.running:
            log.warning("Wifi IDS ya está activo")
            return

        log.info("Iniciando WiFi IDS")

        self.running = True

        self._detector_thread = threading.Thread(
            target=self.detector.start,
            daemon=True
        )

        self._detector_thread.start()

        bus.publish_sync(
            "oled:wifi_status",
            {
                "msg": "IDS activo"
            }
        )

    def stop(self):

        if not self.running:
            return

        log.info("Deteniendo WiFi IDS")

        try:

            self.detector.stop()

        except Exception as e:

            log.error(f"Error deteniendo detector: {e}")

        self.running = False

        bus.publish_sync(
            "oled:wifi_status",
            {
                "msg": "IDS detenido"
            }
        )

        bus.publish_sync(
            "oled:return_menu",
            {}
        )

    def status(self):

        return {

            "running": self.running,

            "channel": getattr(
                self.detector,
                "current_channel",
                None
            ),

            "networks_seen": len(
                getattr(
                    self.detector,
                    "seen_networks",
                    []
                )
            ),

            "evil_twin_on": getattr(
                self.evil_twin,
                "running",
                False
            ),
        }

    # ─────────────────────────────────────
    # HANDLER OLED
    # ─────────────────────────────────────

    def _handle_oled_action(self, event):

        action = event.get(
            "payload",
            {}
        ).get("action")

        if not action:
            return

        log.info(f"[OLED] Acción: {action}")

        try:

            # ───────── IDS ─────────

            if action == "wifi_ids_start":

                bus.publish_sync(
                    "oled:wifi_status",
                    {
                        "msg": "Iniciando IDS..."
                    }
                )

                self.start()

            elif action == "wifi_ids_stop":

                self.stop()

            # ───────── DEAUTH ─────────

            elif action == "wifi_deauth":

                threading.Thread(
                    target=self._run_deauth,
                    daemon=True
                ).start()

            # ───────── BEACON ─────────

            elif action == "wifi_beacon_flood":

                threading.Thread(
                    target=self._run_beacon,
                    daemon=True
                ).start()

            # ───────── EVIL TWIN ─────────

            elif action == "wifi_evil_twin":

                threading.Thread(
                    target=self._run_evil_twin,
                    daemon=True
                ).start()

        except Exception as e:

            log.error(
                f"Error ejecutando acción WiFi: {e}"
            )

            bus.publish_sync(
                "oled:wifi_status",
                {
                    "msg": "Error WiFi"
                }
            )

            bus.publish_sync(
                "oled:return_menu",
                {}
            )

    # ─────────────────────────────────────
    # ATAQUES
    # ─────────────────────────────────────

    def _run_deauth(self):

        with self._attack_lock:

            try:

                bus.publish_sync(
                    "oled:wifi_status",
                    {
                        "msg": "Deauth ejecutando"
                    }
                )

                self.attacker.deauth(
                    "FF:FF:FF:FF:FF:FF"
                )

                bus.publish_sync(
                    "oled:wifi_status",
                    {
                        "msg": "Deauth finalizado"
                    }
                )

            except Exception as e:

                log.error(
                    f"Deauth error: {e}"
                )

                bus.publish_sync(
                    "oled:wifi_status",
                    {
                        "msg": "Error Deauth"
                    }
                )

            finally:

                bus.publish_sync(
                    "oled:return_menu",
                    {}
                )

    def _run_beacon(self):

        with self._attack_lock:

            try:

                bus.publish_sync(
                    "oled:wifi_status",
                    {
                        "msg": "Beacon Flood..."
                    }
                )

                self.attacker.beacon_flood(
                    "FreeWifi"
                )

                bus.publish_sync(
                    "oled:wifi_status",
                    {
                        "msg": "Beacon finalizado"
                    }
                )

            except Exception as e:

                log.error(
                    f"Beacon error: {e}"
                )

                bus.publish_sync(
                    "oled:wifi_status",
                    {
                        "msg": "Error Beacon"
                    }
                )

            finally:

                bus.publish_sync(
                    "oled:return_menu",
                    {}
                )

    def _run_evil_twin(self):

        with self._attack_lock:

            try:

                bus.publish_sync(
                    "oled:wifi_status",
                    {
                        "msg": "Evil Twin..."
                    }
                )

                self.evil_twin.start(
                    "FakeAP",
                    6
                )

                bus.publish_sync(
                    "oled:wifi_status",
                    {
                        "msg": "Evil Twin activo"
                    }
                )

            except Exception as e:

                log.error(
                    f"Evil Twin error: {e}"
                )

                bus.publish_sync(
                    "oled:wifi_status",
                    {
                        "msg": "Error Evil Twin"
                    }
                )

            finally:

                bus.publish_sync(
                    "oled:return_menu",
                    {}
                )

    # ─────────────────────────────────────
    # ALERTAS
    # ─────────────────────────────────────

    def _on_alert(self, event):

        payload = event.get(
            "payload",
            {}
        )

        msg = payload.get(
            "type",
            "Alerta WiFi"
        )

        bus.publish_sync(
            "oled:wifi_status",
            {
                "msg": msg
            }
        )