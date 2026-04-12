import serial
import threading
from core.event_bus import event_bus

class WiFiBridge(threading.Thread):
    def __init__(self, port='/dev/ttyUSB1'): # Asegúrate de que sea el puerto activo
        super().__init__()
        self.port = port
        self.daemon = True
        try:
            self.serial = serial.Serial(port, 115200, timeout=1)
        except:
            self.serial = None

    def run(self):
        if not self.serial: return
        print(f"[*] Escuchando Sonda WiFi en {self.port}...")
        
        while True:
            try:
                line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("WIFI_EVENT:"):
                    parts = line.replace("WIFI_EVENT:", "").split("|")
                    if len(parts) >= 5:
                        data = {
                            "ssid": parts[0],
                            "bssid": parts[1],
                            "rssi": parts[2],
                            "channel": parts[3],
                            "security": parts[4]
                        }
                        event_bus.publish("WIFI_DETECTED", {
                            "module": "WiFi-Scanner",
                            "msg": f"Red detectada: {data['ssid']} ({data['rssi']} dBm)",
                            "data": data
                        })
            except:
                continue