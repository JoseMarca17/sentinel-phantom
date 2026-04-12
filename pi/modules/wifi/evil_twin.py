import os

class EvilTwin:
    def start_ap(self, ssid, interface="wlan0mon"):
        # Configuración básica de hostapd
        conf = f"interface={interface}\ndriver=nl80211\nssid={ssid}\nhw_mode=g\nchannel=6"
        with open("/tmp/hostapd_twin.conf", "w") as f:
            f.write(conf)
        # Lanzar AP (esto requiere root)
        subprocess.Popen(["sudo", "hostapd", "/tmp/hostapd_twin.conf"])