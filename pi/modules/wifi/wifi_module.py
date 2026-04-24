from core.event_bus import bus
from core.logger import get_logger

from modules.wifi.detector import WifiDetector
from modules.wifi.attacker import WifiAttacker
from modules.wifi.pmkid import PmkidAttack
from modules.wifi.evil_twin import EvilTwin
from modules.wifi.sniffer import NetworkSniffer
from modules.wifi.sniffer import NetworkSniffer

import threading

log = get_logger("wifi.module")


class WifiModule:

    def __init__(self, interface="wlan1"):
        self.interface = interface
        self.running   = False

        self.detector  = WifiDetector(interface=interface)
        self.attacker  = WifiAttacker(interface=interface)
        self.pmkid = PmkidAttack(interface=interface)
        self.evil_twin = EvilTwin()
        self.sniffer = NetworkSniffer(interface=interface)
        

        self._detector_thread = None
        self._attack_lock     = threading.Lock()

        # Estado para el flujo scan → selección → ataque
        self._scanned_nets:   list = []
        self._pending_attack: str  = ""  # "deauth" | "beacon" | "pmkid"

        bus.subscribe("oled:action", self._handle_oled_action)
        bus.subscribe("wifi.alert",  self._on_alert)

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
        bus.publish_sync("oled:wifi_status", {"msg": "IDS activo"})

    def stop(self):
        if not self.running:
            return

        log.info("Deteniendo WiFi IDS")
        try:
            self.detector.stop()
        except Exception as e:
            log.error(f"Error deteniendo detector: {e}")

        self.running = False
        bus.publish_sync("oled:wifi_status", {"msg": "IDS detenido"})
        bus.publish_sync("oled:return_menu", {})

    def status(self):
        return {
            "running":       self.running,
            "channel":       getattr(self.detector, "current_channel", None),
            "networks_seen": len(getattr(self.detector, "seen_networks", [])),
            "evil_twin_on":  getattr(self.evil_twin, "running", False),
        }

    # ─────────────────────────────────────
    # HANDLER OLED
    # ─────────────────────────────────────

    def _handle_oled_action(self, event):
        action = event.get("payload", {}).get("action")
        if not action:
            return

        log.info(f"[OLED] Acción: {action}")

        try:
            # ── IDS ──────────────────────────────────────────────────────────
            if action == "wifi_ids_start":
                bus.publish_sync("oled:wifi_status", {"msg": "Iniciando IDS..."})
                self.start()

            elif action == "wifi_ids_stop":
                self.stop()

            # ── ATAQUES paso 1: escanear y mostrar redes ──────────────────────
            elif action in ("wifi_deauth", "wifi_beacon_flood", "wifi_pmkid"):
                self._pending_attack = {
                    "wifi_deauth":       "deauth",
                    "wifi_beacon_flood": "beacon",
                    "wifi_pmkid":        "pmkid",
                }[action]

                threading.Thread(
                    target=self._scan_and_show_nets,
                    daemon=True
                ).start()

            # ── ATAQUES paso 2: ejecutar tras selección de red ────────────────
            elif action == "wifi_do_deauth":
                net_idx = event["payload"].get("net_idx", 0)
                threading.Thread(
                    target=self._run_deauth,
                    args=(net_idx,),
                    daemon=True
                ).start()

            elif action == "wifi_do_beacon":
                net_idx = event["payload"].get("net_idx", 0)
                threading.Thread(
                    target=self._run_beacon,
                    args=(net_idx,),
                    daemon=True
                ).start()

            elif action == "wifi_do_pmkid":
                net_idx = event["payload"].get("net_idx", 0)
                threading.Thread(
                    target=self._run_pmkid,
                    args=(net_idx,),
                    daemon=True
                ).start()

            # ── EVIL TWIN ─────────────────────────────────────────────────────
            elif action == "wifi_evil_twin":
                threading.Thread(
                    target=self._run_evil_twin,
                    daemon=True
                ).start()
            
            elif action == "wifi_sniffer_start":
                threading.Thread(
                    target=self.sniffer.start,
                    args=(20,),   # 20 segundos
                    daemon=True
                ).start()

            elif action == "wifi_sniffer_stop":
                self.sniffer.stop()
                bus.publish_sync("oled:wifi_status", {"msg": "Sniffer OFF"})
                time.sleep(0.8)
                bus.publish_sync("oled:return_menu", {})

        except Exception as e:
            log.error(f"Error ejecutando acción WiFi: {e}")
            bus.publish_sync("oled:wifi_status", {"msg": "Error WiFi"})
            bus.publish_sync("oled:return_menu", {})

    # ─────────────────────────────────────
    # SCAN → OLED SELECT
    # ─────────────────────────────────────

    def _scan_and_show_nets(self):
        """
        Escanea redes y publica oled:wifi_nets para que el OLED
        muestre el menú de selección. Cada red lleva attack_action
        para que el OLED sepa qué disparar al confirmar.
        """
        nets = self.attacker.scan_networks(include_5ghz=False)

        if not nets:
            bus.publish_sync("oled:wifi_status", {"msg": "Sin redes"})
            import time; time.sleep(1.5)
            bus.publish_sync("oled:return_menu", {})
            return

        self._scanned_nets = nets

        action_map = {
            "deauth": "wifi_do_deauth",
            "beacon": "wifi_do_beacon",
            "pmkid":  "wifi_do_pmkid",
        }

        formatted = [
            {
                "ssid":          n.get("ssid",    "??"),
                "ch":            n.get("channel", 0),
                "rssi":          n.get("rssi",    -99),
                "bssid":         n.get("bssid",   ""),
                "attack_action": action_map.get(self._pending_attack, "wifi_do_deauth"),
            }
            for n in nets
        ]

        bus.publish_sync("oled:wifi_nets", {"networks": formatted})

    # ─────────────────────────────────────
    # ATAQUES REALES
    # ─────────────────────────────────────

    def _run_deauth(self, net_idx: int = 0):
        with self._attack_lock:
            try:
                if not self._scanned_nets:
                    log.error("No hay redes escaneadas")
                    bus.publish_sync("oled:wifi_status", {"msg": "Sin red"})
                    return

                net     = self._scanned_nets[net_idx]
                bssid   = net.get("bssid",   "")
                ssid    = net.get("ssid",    "??")
                channel = net.get("channel", None)

                if not bssid:
                    bus.publish_sync("oled:wifi_status", {"msg": "BSSID inválido"})
                    return

                log.warning(f"Deauth → {ssid} ({bssid}) canal:{channel}")
                bus.publish_sync("oled:wifi_status", {"msg": f"Deauth {ssid[:12]}"})
                self.attacker.deauth(bssid=bssid, channel=channel)
                event_data = {
                    "type": "deauth_attack",
                    "module": "wifi",
                    "data": {"target": ssid, "bssid": bssid},
                    "severity": "high"
                }
                bus.publish("wifi:event", event_data)
            except IndexError:
                log.error(f"net_idx {net_idx} fuera de rango")
                bus.publish_sync("oled:wifi_status", {"msg": "Índice inválido"})
            except Exception as e:
                log.error(f"Deauth error: {e}")
                bus.publish_sync("oled:wifi_status", {"msg": "Error Deauth"})
            finally:
                bus.publish_sync("oled:return_menu", {})

    def _run_beacon(self, net_idx: int = 0):
        with self._attack_lock:
            try:
                if not self._scanned_nets:
                    log.error("No hay redes escaneadas")
                    bus.publish_sync("oled:wifi_status", {"msg": "Sin red"})
                    return

                net     = self._scanned_nets[net_idx]
                ssid    = net.get("ssid",    "FreeWifi")
                channel = net.get("channel", 6) or 6  # 0/None → 6

                log.warning(f"Beacon flood → SSID:{ssid} ch:{channel}")
                self.attacker.beacon_flood(ssid=ssid, channel=channel)

            except IndexError:
                log.error(f"net_idx {net_idx} fuera de rango")
                bus.publish_sync("oled:wifi_status", {"msg": "Índice inválido"})
            except Exception as e:
                log.error(f"Beacon error: {e}")
                bus.publish_sync("oled:wifi_status", {"msg": "Error Beacon"})
            finally:
                bus.publish_sync("oled:return_menu", {})

    def _run_pmkid(self, net_idx: int = 0):
        with self._attack_lock:
            try:
                if not self._scanned_nets:
                    log.error("No hay redes escaneadas")
                    bus.publish_sync("oled:wifi_status", {"msg": "Sin red"})
                    return

                net   = self._scanned_nets[net_idx]
                bssid = net.get("bssid", "")
                ssid  = net.get("ssid",  "??")

                if not bssid:
                    bus.publish_sync("oled:wifi_status", {"msg": "BSSID inválido"})
                    return

                log.warning(f"PMKID → {ssid} ({bssid})")
                bus.publish_sync("oled:wifi_status", {"msg": f"PMKID {ssid[:12]}"})
                self.pmkid.capture(bssid=bssid)

            except IndexError:
                log.error(f"net_idx {net_idx} fuera de rango")
                bus.publish_sync("oled:wifi_status", {"msg": "Índice inválido"})
            except Exception as e:
                log.error(f"PMKID error: {e}")
                bus.publish_sync("oled:wifi_status", {"msg": "Error PMKID"})
            finally:
                bus.publish_sync("oled:return_menu", {})

    def _run_evil_twin(self):
        with self._attack_lock:
            try:
                bus.publish_sync("oled:wifi_status", {"msg": "Evil Twin..."})
                self.evil_twin.start("FakeAP", 6)
                bus.publish_sync("oled:wifi_status", {"msg": "Evil Twin activo"})
            except Exception as e:
                log.error(f"Evil Twin error: {e}")
                bus.publish_sync("oled:wifi_status", {"msg": "Error Evil Twin"})
            finally:
                bus.publish_sync("oled:return_menu", {})

    # ─────────────────────────────────────
    # ALERTAS IDS
    # ─────────────────────────────────────

    def _on_alert(self, event):
        msg = event.get("payload", {}).get("type", "Alerta WiFi")
        bus.publish_sync("oled:wifi_status", {"msg": msg})