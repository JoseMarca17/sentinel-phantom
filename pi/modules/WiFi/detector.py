from scapy.all import sniff, Dot11, Dot11Deauth, Dot11Beacon
from collections import defaultdict
from datetime import datetime
from core.event_bus import EventBus
from core.logger import get_logger
import threading
import subprocess
import time

log = get_logger("wifi.detector")
bus = EventBus()

class WiFiDetector:
    def __init__(self, interface='wlan1'):
        self.interface = interface
        self.running = False
        self.current_channel = 1
        self.CHANNELS = list(range(1, 12))
        self.HOP_INTERVAL = 3
        self.beacon_window = defaultdict(list)
        self.BEACON_THRESHOLD = 50
        self.seen_networks = set()
        self.known_aps = {}

    def add_known_ap(self, bssid: str, ssid: str):
        self.known_aps[bssid.upper()] = ssid
        log.info(f"AP conocido: {ssid} ({bssid})")

    def _enable_monitor_mode(self):
        log.info(f"Activando modo monitor en {self.interface}...")
        subprocess.run(['sudo', 'ip', 'link', 'set', self.interface, 'down'], capture_output=True)
        subprocess.run(['sudo', 'iw', 'dev', self.interface, 'set', 'type', 'monitor'], capture_output=True)
        subprocess.run(['sudo', 'ip', 'link', 'set', self.interface, 'up'], capture_output=True)
        result = subprocess.run(['iw', 'dev', self.interface, 'info'], capture_output=True, text=True)
        if 'monitor' in result.stdout:
            log.info("Modo monitor activo.")
            return True
        log.error("No se pudo activar modo monitor.")
        return False

    def _channel_hopper(self):
        while self.running:
            for ch in self.CHANNELS:
                if not self.running:
                    break
                self.current_channel = ch
                subprocess.run(
                    ['sudo', 'iwconfig', self.interface, 'channel', str(ch)],
                    capture_output=True
                )
                log.debug(f"Canal → {ch}")
                time.sleep(self.HOP_INTERVAL)

    def _process_packet(self, pkt):
        if pkt.haslayer(Dot11Deauth):
            self._handle_deauth(pkt)
        elif pkt.haslayer(Dot11Beacon):
            self._handle_beacon(pkt)

    def _handle_deauth(self, pkt):
        source = pkt[Dot11].addr2 or 'desconocido'
        target = pkt[Dot11].addr1 or 'desconocido'
        reason = pkt[Dot11Deauth].reason
        payload = {
            'timestamp':  datetime.now().isoformat(),
            'type':       'deauth_detected',
            'severity':   'critical',
            'source_mac': source,
            'target_mac': target,
            'reason':     reason,
            'channel':    self.current_channel,
        }
        log.warning(f"DEAUTH | {source} → {target} | CH {self.current_channel}")
        bus.publish_sync('wifi.alert', payload)

    def _handle_beacon(self, pkt):
        now = time.time()
        try:
            stats   = pkt[Dot11Beacon].network_stats()
            ssid    = stats.get('ssid', 'unknown')
            channel = stats.get('channel', self.current_channel)
            crypto  = stats.get('crypto', set())
            bssid   = (pkt[Dot11].addr3 or 'unknown').upper()
        except Exception:
            return

        if bssid not in self.seen_networks:
            self.seen_networks.add(bssid)
            for known_bssid, known_ssid in self.known_aps.items():
                if ssid == known_ssid and bssid != known_bssid:
                    payload = {
                        'timestamp':  datetime.now().isoformat(),
                        'type':       'evil_twin_detected',
                        'severity':   'critical',
                        'ssid':       ssid,
                        'fake_bssid': bssid,
                        'real_bssid': known_bssid,
                        'channel':    self.current_channel,
                    }
                    log.warning(f"EVIL TWIN | {ssid} | BSSID falso: {bssid}")
                    bus.publish_sync('wifi.alert', payload)
                    return
            log.info(f"RED | {ssid:<25} {bssid}  CH:{channel}  {crypto}")

        self.beacon_window[ssid].append(now)
        self.beacon_window[ssid] = [
            t for t in self.beacon_window[ssid] if now - t < 1.0
        ]
        if len(self.beacon_window[ssid]) > self.BEACON_THRESHOLD:
            payload = {
                'timestamp': datetime.now().isoformat(),
                'type':      'beacon_flood_detected',
                'severity':  'warning',
                'ssid':      ssid,
                'count':     len(self.beacon_window[ssid]),
                'channel':   self.current_channel,
            }
            log.warning(f"BEACON FLOOD | {ssid} | {len(self.beacon_window[ssid])}/s")
            bus.publish_sync('wifi.alert', payload)
            self.beacon_window[ssid] = []

    def start(self):
        self._enable_monitor_mode()
        log.info(f"Iniciando en {self.interface} | Canales {self.CHANNELS}")
        self.running = True
        hop_thread = threading.Thread(target=self._channel_hopper, daemon=True)
        hop_thread.start()
        sniff(
            iface=self.interface,
            prn=self._process_packet,
            store=False,
            stop_filter=lambda p: not self.running
        )

    def stop(self):
        self.running = False
        log.info("Detector detenido.")


if __name__ == '__main__':
    detector = WiFiDetector(interface='wlan1')
    detector.start()
