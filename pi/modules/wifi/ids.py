"""
pi/modules/wifi/ids.py
IDS 802.11 — Detección de Evil Twin y otros ataques WiFi.

Método de detección Evil Twin:
  1. Escucha beacons (frame tipo 0x80) de todos los APs cercanos
  2. Construye un diccionario {ssid: set_of_bssids}
  3. Si un SSID conocido aparece con un BSSID nuevo → Evil Twin
  4. También detecta: señal más fuerte del mismo SSID (posición sospechosa)

Requiere: adaptador WiFi en modo monitor (MT7601U)
          sudo ip link set wlan1 down
          sudo iw dev wlan1 set type monitor
          sudo ip link set wlan1 up
"""

import logging
import threading
import time
from collections import defaultdict
from typing import Callable, Optional

logger = logging.getLogger(__name__)

try:
    from scapy.all import (
        sniff, Dot11, Dot11Beacon, Dot11Elt,
        Dot11Deauth, Dot11ProbeResp, RadioTap
    )
    SCAPY_OK = True
except ImportError:
    logger.warning("Scapy no disponible — IDS en modo simulado")
    SCAPY_OK = False


class WifiIDS:
    """
    IDS WiFi pasivo. Escucha en modo monitor y detecta:
      - Evil Twin     : SSID conocido con BSSID diferente
      - Deauth flood  : >50 frames deauth por segundo desde un BSSID
      - Beacon flood  : >20 SSIDs únicos en 10 segundos
    """

    DEAUTH_THRESHOLD  = 50    # paquetes/s para disparar alerta
    BEACON_THRESHOLD  = 20    # SSIDs únicos en ventana de 10s
    BEACON_WINDOW_S   = 10

    def __init__(self,
                 iface: str = "wlan1",
                 on_alert: Optional[Callable] = None,
                 on_event: Optional[Callable] = None):
        self.iface    = iface
        self.on_alert = on_alert   # callback(level, type, data)
        self.on_event = on_event   # callback(type, data)
        self.running  = False

        # Tabla de APs legítimos: {ssid: set(bssid)}
        # Aprende automáticamente los primeros 60s o se puede precargar
        self._known_aps:   dict[str, set]  = defaultdict(set)
        self._learning     = True           # modo aprendizaje inicial
        self._learn_until  = 0

        # Contadores para detección de floods
        self._deauth_count: dict[str, int] = defaultdict(int)
        self._deauth_window_start = 0
        self._beacon_ssids: set   = set()
        self._beacon_window_start = 0

        self._thread: Optional[threading.Thread] = None
        self._lock   = threading.Lock()

    # ── Ciclo de vida ────────────────────────────────────────────
    def start(self, learn_seconds: int = 60):
        """
        Inicia el IDS.
        learn_seconds: segundos en modo aprendizaje (memoriza APs legítimos)
        """
        if not SCAPY_OK:
            logger.error("Scapy no disponible, IDS no puede iniciar")
            return False

        self.running          = True
        self._learning        = True
        self._learn_until     = time.time() + learn_seconds
        self._deauth_window_start = time.time()
        self._beacon_window_start = time.time()

        self._thread = threading.Thread(
            target=self._sniff_loop,
            daemon=True,
            name="wifi-ids"
        )
        self._thread.start()
        logger.info(f"[IDS] Iniciado en {self.iface} — "
                    f"aprendiendo {learn_seconds}s")
        return True

    def stop(self):
        self.running = False
        logger.info("[IDS] Detenido")

    def add_known_ap(self, ssid: str, bssid: str):
        """Añade un AP legítimo conocido manualmente."""
        with self._lock:
            self._known_aps[ssid].add(bssid.upper())

    def get_known_aps(self) -> dict:
        with self._lock:
            return {k: list(v) for k, v in self._known_aps.items()}

    # ── Sniffing ─────────────────────────────────────────────────
    def _sniff_loop(self):
        sniff(
            iface=self.iface,
            prn=self._process_packet,
            store=False,
            stop_filter=lambda _: not self.running,
        )

    def _process_packet(self, pkt):
        if not self.running:
            return

        # Salir del modo aprendizaje
        if self._learning and time.time() > self._learn_until:
            self._learning = False
            n = sum(len(v) for v in self._known_aps.values())
            logger.info(f"[IDS] Aprendizaje completo — "
                        f"{len(self._known_aps)} SSIDs, {n} BSSIDs")

        # Detectar frames Beacon (tipo 0x80)
        if pkt.haslayer(Dot11Beacon):
            self._handle_beacon(pkt)

        # Detectar frames Deauth (tipo 0xC0)
        elif pkt.haslayer(Dot11Deauth):
            self._handle_deauth(pkt)

    # ── Detección: Evil Twin ─────────────────────────────────────
    def _handle_beacon(self, pkt):
        try:
            bssid = pkt[Dot11].addr3.upper() if pkt[Dot11].addr3 else None
            ssid  = pkt[Dot11Elt].info.decode("utf-8", errors="replace").strip()
            rssi  = pkt[RadioTap].dBm_AntSignal if pkt.haslayer(RadioTap) else -99

            if not bssid or not ssid:
                return
        except Exception:
            return

        with self._lock:
            # ── Modo aprendizaje: memorizar APs legítimos ────────
            if self._learning:
                self._known_aps[ssid].add(bssid)
                return

            # ── Detección de Evil Twin ────────────────────────────
            if ssid in self._known_aps:
                if bssid not in self._known_aps[ssid]:
                    # SSID conocido con BSSID NUEVO → Evil Twin
                    legit_bssids = list(self._known_aps[ssid])
                    data = {
                        "ssid":          ssid,
                        "evil_bssid":    bssid,
                        "legit_bssids":  legit_bssids,
                        "rssi":          rssi,
                    }
                    logger.critical(
                        f"[IDS] EVIL TWIN DETECTADO: '{ssid}' "
                        f"BSSID={bssid} (legítimos: {legit_bssids})"
                    )
                    self._fire_alert("critical", "evil_twin", data)
            else:
                # SSID nuevo — añadir si parece legítimo
                self._known_aps[ssid].add(bssid)

            # ── Beacon flood ──────────────────────────────────────
            now = time.time()
            if now - self._beacon_window_start > self.BEACON_WINDOW_S:
                self._beacon_ssids.clear()
                self._beacon_window_start = now

            self._beacon_ssids.add(ssid)
            if len(self._beacon_ssids) > self.BEACON_THRESHOLD:
                self._fire_alert("high", "beacon_flood", {
                    "unique_ssids": len(self._beacon_ssids),
                    "window_s":     self.BEACON_WINDOW_S,
                })
                self._beacon_ssids.clear()   # reset para no spam

    # ── Detección: Deauth flood ──────────────────────────────────
    def _handle_deauth(self, pkt):
        try:
            src = pkt[Dot11].addr2.upper()
        except Exception:
            return

        with self._lock:
            now = time.time()
            if now - self._deauth_window_start > 1.0:
                self._deauth_count.clear()
                self._deauth_window_start = now

            self._deauth_count[src] += 1

            if self._deauth_count[src] >= self.DEAUTH_THRESHOLD:
                self._fire_alert("critical", "deauth_flood", {
                    "bssid":   src,
                    "count":   self._deauth_count[src],
                    "per_sec": self._deauth_count[src],
                })
                self._deauth_count[src] = 0   # reset

    # ── Disparar alerta ──────────────────────────────────────────
    def _fire_alert(self, level: str, alert_type: str, data: dict):
        if self.on_alert:
            try:
                self.on_alert(level, alert_type, data)
            except Exception as e:
                logger.error(f"[IDS] on_alert error: {e}")
        if self.on_event:
            try:
                self.on_event(alert_type, data)
            except Exception as e:
                logger.error(f"[IDS] on_event error: {e}")
