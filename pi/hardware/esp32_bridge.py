import serial
import threading
from core.event_bus import event_bus

class ESP32Bridge(threading.Thread):
    def __init__(self, port='/dev/ttyUSB0'): # Cambia a 'COMX' en Windows
        super().__init__()
        self.port = port
        self.serial = serial.Serial(port, 115200, timeout=1)
        self.daemon = True

    def run(self):
        print(f"[*] Escuchando Sonda ESP32 en {self.port}...")
        while True:
            line = self.serial.readline().decode('utf-8').strip()
            if line.startswith("RFID_CAPTURE:"):
                uid = line.split(":")[1]
                # Inyectamos el evento al sistema como si fuera hardware local
                event_bus.publish("RFID_DETECTED", {
                    "module": "ESP32-Remote-Probe",
                    "msg": f"UID Capturado vía RF: {uid}",
                    "data": uid
                })