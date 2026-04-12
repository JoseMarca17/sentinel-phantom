from .attacker import WiFiAttacker
from .wps_scan import WPSScanner

class WiFiModule:
    def __init__(self):
        self.attacker = WiFiAttacker()
        self.wps = WPSScanner()

    def audit_network(self, bssid):
        print(f"[*] Iniciando auditoría completa sobre {bssid}")
        # Lógica para elegir el mejor ataque automáticamente