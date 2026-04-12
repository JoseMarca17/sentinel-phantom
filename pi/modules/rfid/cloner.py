from core.event_bus import event_bus
import time

class RFIDCloner:
    """Módulo especializado en volcado y escritura de sectores Mifare."""
    
    def __init__(self):
        event_bus.subscribe(self.handle_events)

    def handle_events(self, event_type, data):
        if event_type == "RFID_DETECTED":
            print(f"[*] Cloner: Preparando volcado de datos para UID {data['data']}...")
            self.attempt_clone(data['data'])

    def attempt_clone(self, uid):
        # Según el Anexo B, esto debe durar menos de 5 segundos [cite: 188]
        print(f"[!] Iniciando ataque de fuerza bruta a sectores Mifare...")
        time.sleep(1.5) # Simulación de crackeo de llaves A/B
        print(f"[OK] Sectores vulnerables volcados. Listo para replicar en tarjeta virgen.")