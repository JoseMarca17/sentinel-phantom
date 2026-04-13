import subprocess
import re
import json
import requests
from core.logger import get_logger
from core.event_bus import event_bus
from config import config

logger = get_logger('tscm.scanner')

# OUIs conocidos de cámaras IP y micrófonos inalámbricos
SUSPICIOUS_OUIS = {
    'D8:BB:C1': 'Hikvision',
    '44:19:B6': 'Hikvision',
    'BC:AD:28': 'Dahua',
    'E0:50:8B': 'Dahua',
    'B4:A2:EB': 'TP-Link Camera',
    '50:D4:F7': 'Wyze Camera',
    'AC:63:BE': 'Amcrest',
    '00:18:AE': 'Axis Camera',
}

class TSCMScanner:
    def __init__(self):
        self.iface    = config.WIFI_IFACE
        self._devices = {}

    def scan(self) -> list[dict]:
        """Escanea dispositivos 2.4GHz con OUI fingerprinting."""
        logger.info("TSCM scan iniciado")
        raw_networks = self._iwlist_scan()
        results      = []

        for net in raw_networks:
            mac    = net.get('mac', '').upper()
            oui    = ':'.join(mac.split(':')[:3])
            vendor = SUSPICIOUS_OUIS.get(oui)

            entry = {
                'mac':        mac,
                'ssid':       net.get('ssid', ''),
                'channel':    net.get('channel', 0),
                'signal':     net.get('signal', -100),
                'oui':        oui,
                'vendor':     vendor or self._lookup_oui(oui),
                'suspicious': vendor is not None
            }
            results.append(entry)
            self._devices[mac] = entry

            if entry['suspicious']:
                logger.warning(f"Dispositivo sospechoso: {mac} ({entry['vendor']})")
                event_bus.publish('tscm.alert', {
                    'type':    'suspicious_device',
                    'mac':     mac,
                    'vendor':  entry['vendor'],
                    'ssid':    entry['ssid'],
                    'severity': 'high'
                })

        event_bus.publish('tscm.scan_complete', {'count': len(results), 'devices': results})
        return results

    def _iwlist_scan(self) -> list[dict]:
        try:
            result = subprocess.run(
                ['iwlist', self.iface, 'scan'],
                capture_output=True, text=True, timeout=15
            )
            return self._parse_iwlist(result.stdout)
        except Exception as e:
            logger.error(f"iwlist scan falló: {e}")
            return []

    def _parse_iwlist(self, output: str) -> list[dict]:
        networks = []
        current  = {}
        for line in output.splitlines():
            line = line.strip()
            if 'Address:' in line:
                if current:
                    networks.append(current)
                current = {'mac': line.split('Address:')[-1].strip()}
            elif 'ESSID:' in line:
                current['ssid'] = line.split('ESSID:')[-1].strip().strip('"')
            elif 'Channel:' in line:
                try:
                    current['channel'] = int(re.search(r'\d+', line).group())
                except Exception:
                    pass
            elif 'Signal level' in line:
                try:
                    match = re.search(r'Signal level=(-?\d+)', line)
                    if match:
                        current['signal'] = int(match.group(1))
                except Exception:
                    pass
        if current:
            networks.append(current)
        return networks

    def _lookup_oui(self, oui: str) -> str:
        """Lookup online de OUI (fallback si no está en la lista local)."""
        try:
            clean = oui.replace(':', '').upper()
            resp  = requests.get(
                f'https://api.macvendors.com/{clean}',
                timeout=3
            )
            return resp.text.strip() if resp.status_code == 200 else 'Unknown'
        except Exception:
            return 'Unknown'

    def get_devices(self) -> dict:
        return self._devices