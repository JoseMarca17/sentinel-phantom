from core.event_bus import EventBus
from core.logger import get_logger
from modules.wifi.detector import WiFiDetector
from modules.wifi.attacker import WifiAttacker
from modules.wifi.pmkid import PMKIDCapture
from modules.wifi.evil_twin import EvilTwin
import threading

log = get_logger("wifi.module")
bus = EventBus()

class WifiModule:
    def __init__(self, interface='wlan1'):
        self.interface = interface
        self.running = False

        # Submodulos
        self.detector   = WiFiDetector(interface=interface)
        self.attacker   = WifiAttacker(interface=interface)
        self.pmkid      = PMKIDCapture(interface=interface)
        self.evil_twin  = EvilTwin(interface='wlan0')

        # Hilo del detector
        self._detector_thread = None

        # Suscribirse a alertas para loggearlas
        bus.subscribe('wifi.alert', self._on_alert)

    def start(self) -> bool:
        """Arranca el modulo WiFi completo"""
        log.info("Iniciando modulo WiFi...")
        self.running = True

        # Arrancar detector en hilo separado
        self._detector_thread = threading.Thread(
            target=self.detector.start,
            daemon=True
        )
        self._detector_thread.start()

        bus.publish_sync('wifi.module_started', {
            'interface': self.interface,
            'status':    'running',
        })
        log.info("Modulo WiFi activo.")
        return True

    def stop(self):
        """Detiene todo el modulo WiFi"""
        log.info("Deteniendo modulo WiFi...")
        self.detector.stop()

        if self.evil_twin.running:
            self.evil_twin.stop()

        self.running = False
        bus.publish_sync('wifi.module_stopped', {'status': 'stopped'})
        log.info("Modulo WiFi detenido.")

    def get_status(self) -> dict:
        return {
            'running':          self.running,
            'interface':        self.interface,
            'detector_running': self.detector.running,
            'evil_twin_active': self.evil_twin.running,
            'redes_vistas':     len(self.detector.seen_networks),
        }

    # ── Acciones del atacante ─────────────────────────────────────────────

    def scan_wps(self) -> list:
        """Escanea redes con WPS habilitado"""
        return self.attacker.wps_scan()

    def do_deauth(self, bssid: str, client: str = 'FF:FF:FF:FF:FF:FF', count: int = 10) -> bool:
        """Envia deauth contra un AP"""
        return self.attacker.deauth(bssid, client, count)

    def do_beacon_flood(self, ssid: str) -> bool:
        """Lanza beacon flood con un SSID falso"""
        return self.attacker.beacon_flood(ssid)

    def do_pmkid(self, bssid: str, timeout: int = 30):
        """Captura PMKID de un AP"""
        return self.pmkid.capture(bssid, timeout)

    def do_evil_twin(self, ssid: str, channel: int = 6) -> bool:
        """Levanta un Evil Twin con el SSID dado"""
        return self.evil_twin.start(ssid, channel)

    def stop_evil_twin(self):
        """Detiene el Evil Twin"""
        self.evil_twin.stop()

    def add_known_ap(self, bssid: str, ssid: str):
        """Agrega un AP legitimo para deteccion de Evil Twin"""
        self.detector.add_known_ap(bssid, ssid)

    # ── Handlers de eventos ───────────────────────────────────────────────

    def _on_alert(self, event: dict):
        payload = event.get('payload', {})
        severity = payload.get('severity', 'info')
        tipo     = payload.get('type', 'unknown')
        log.warning(f"[ALERTA] {severity.upper()} | {tipo} | {payload}")
