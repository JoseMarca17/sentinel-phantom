"""
run_detector.py — Corre el WiFiDetector standalone
Proyecto: Centinela MK1

Uso:
    sudo python run_detector.py

Antes de correr, buscar el BSSID del AP real:
    sudo iw dev wlan1 scan | grep -E "BSS |SSID:"
"""

from core.event_bus import bus
from modules.WiFi.detector import WiFiDetector

INTERFACE = "wlan1"

KNOWN_APS = [
    # ("AA:BB:CC:DD:EE:FF", "EMI_Laboratorio"),
]


def _on_alert(event: dict):
    payload    = event.get("payload", {})
    alert_type = payload.get("type", "?")
    severity   = payload.get("severity", "info")
    tag        = "🚨 CRITICO" if severity == "critical" else "⚠  WARNING"
    print(f"\n{tag} [{alert_type}]")
    print(f"  SSID      : {payload.get('ssid', '-')}")
    print(f"  BSSID fake: {payload.get('fake_bssid', '-')}")
    print(f"  BSSID real: {payload.get('real_bssid', '-')}")
    print(f"  Canal     : {payload.get('channel', '-')}")
    print(f"  RSSI      : {payload.get('rssi', '-')} dBm")
    print(f"  Detalle   : {payload.get('detail', '-')}\n")


def main():
    bus.subscribe("wifi.alert", _on_alert)

    detector = WiFiDetector(interface=INTERFACE)

    for bssid, ssid in KNOWN_APS:
        detector.add_known_ap(bssid, ssid)

    print(f"[*] Detector iniciando en {INTERFACE}")
    print(f"[*] APs conocidos: {len(KNOWN_APS)}")
    print("[*] Ctrl+C para detener\n")

    try:
        detector.start()
    except KeyboardInterrupt:
        detector.stop()
        print("\n[*] Detector detenido")


if __name__ == '__main__':
    main()
