import threading
from scapy.all import sniff, Dot11, Dot11Beacon, Dot11Deauth, Dot11ProbeResp, RadioTap
from collections import defaultdict
from core.logger import get_logger
from core.event_bus import event_bus
from config import config

logger = get_logger('wifi.ids')

DEAUTH_THRESHOLD    = 5   # deauths por segundo para alertar
BEACON_FLOOD_THRESH = 20  # beacons distintos por segundo

class WifiIDS:
    def __init__(self):
        self.iface          = config.WIFI_IFACE
        self._running       = False
        self._thread        = None
        self._deauth_count  = defaultdict(int)
        self._beacon_macs   = set()
        self._known_aps     = {}   # bssid → ssid legítimos
        self._lock          = threading.Lock()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._sniff_loop, daemon=True)
        self._thread.start()
        logger.info(f"IDS WiFi iniciado en {self.iface}")

    def stop(self) -> None:
        self._running = False
        logger.info("IDS WiFi detenido")

    def add_known_ap(self, bssid: str, ssid: str) -> None:
        self._known_aps[bssid.lower()] = ssid

    def _sniff_loop(self) -> None:
        sniff(
            iface=self.iface,
            prn=self._process_packet,
            store=False,
            stop_filter=lambda _: not self._running
        )

    def _process_packet(self, pkt) -> None:
        if pkt.haslayer(Dot11Deauth):
            self._handle_deauth(pkt)
        elif pkt.haslayer(Dot11Beacon):
            self._handle_beacon(pkt)

    def _handle_deauth(self, pkt) -> None:
        src = pkt[Dot11].addr2 or 'unknown'
        with self._lock:
            self._deauth_count[src] += 1
            count = self._deauth_count[src]

        if count >= DEAUTH_THRESHOLD:
            logger.warning(f"Ataque deauth detectado desde {src} ({count} frames)")
            event_bus.publish('wifi.alert', {
                'type':    'deauth_attack',
                'source':  src,
                'count':   count,
                'severity': 'high'
            })
            with self._lock:
                self._deauth_count[src] = 0

    def _handle_beacon(self, pkt) -> None:
        bssid = pkt[Dot11].addr3 or ''
        try:
            ssid = pkt[Dot11Beacon].info.decode('utf-8', errors='ignore')
        except Exception:
            ssid = ''

        # Evil twin: mismo SSID, distinto BSSID
        for known_bssid, known_ssid in self._known_aps.items():
            if ssid == known_ssid and bssid.lower() != known_bssid:
                logger.warning(f"Posible evil twin: SSID={ssid} BSSID={bssid}")
                event_bus.publish('wifi.alert', {
                    'type':     'evil_twin',
                    'ssid':     ssid,
                    'bssid':    bssid,
                    'severity': 'critical'
                })

        # Beacon flood: muchos BSSIDs distintos
        with self._lock:
            self._beacon_macs.add(bssid)
            count = len(self._beacon_macs)

        if count >= BEACON_FLOOD_THRESH:
            logger.warning(f"Beacon flood detectado: {count} BSSIDs únicos")
            event_bus.publish('wifi.alert', {
                'type':     'beacon_flood',
                'count':    count,
                'severity': 'medium'
            })
            with self._lock:
                self._beacon_macs.clear()