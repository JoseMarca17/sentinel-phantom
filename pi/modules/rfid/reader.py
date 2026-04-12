import time
from core.base_module import BaseModule
from core.event_bus import event_bus
from config import DEBUG_MODE

class RFIDModule(BaseModule):
    def __init__(self):
        super().__init__("RFID-Engine")
        self.pn532 = None
        self._setup_hardware()

    def _setup_hardware(self):
        if not DEBUG_MODE:
            try:
                from py532.nfc import NfcAdapter
                self.pn532 = NfcAdapter()
                print("[+] Hardware PN532 inicializado correctamente.")
            except Exception as e:
                print(f"[!] Error cargando hardware real: {e}")
                
    def run(self):
        self.is_running = True
        self.log_event("Iniciando monitoreo de proximidad 13.56MHz", level="INFO")
        
        while self.is_running:
            uid = self._read_passive_target()
            
            if uid:
                # El Anexo B pide mitigar accesos no autorizados [cite: 85]
                self.log_event(f"¡Tarjeta Capturada! UID: {uid}", level="CRITICAL")
                
                # Publicar al EventBus para que el OLED y la DB se enteren
                event_bus.publish("RFID_DETECTED", {
                    "module": self.name,
                    "msg": f"UID: {uid}",
                    "data": uid
                })
                
                # Evitar lecturas duplicadas inmediatas
                time.sleep(2)
            
            time.sleep(0.5)

    def _read_passive_target(self):
        """Lee el UID de la tarjeta."""
        if DEBUG_MODE:
            # SIMULACIÓN: Presiona Enter en la terminal para "simular" una tarjeta
            # Esto te permite probar la integración sin el sensor
            val = input("\n[SIMULADOR] Presiona 'k' para simular lectura de tarjeta: ")
            if val.lower() == 'k':
                return "DE:AD:BE:EF:01"
            return None
        else:
            # LÓGICA REAL PARA RASPBERRY PI
            try:
                # Lectura rápida para cumplir latencia < 2s 
                return self.pn532.scan_field().hex(':').upper()
            except:
                return None