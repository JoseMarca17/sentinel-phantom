from scapy.all import *

class WiFiIDS:
    def detect_deauth(self, pkt):
        if pkt.haslayer(Dot11Deauth):
            print(f"[!] ALERTA: Intento de Deauth detectado desde {pkt.addr2}")

    def start_monitoring(self, interface="wlan0mon"):
        sniff(iface=interface, prn=self.detect_deauth, store=0)