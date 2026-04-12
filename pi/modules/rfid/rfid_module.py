from core.base_module import BaseModule
from .reader import RFIDModule as ReaderEngine
from .cloner import RFIDCloner

class RFIDTopModule(BaseModule):
    """
    Orquestador de Nivel Superior para RFID/NFC.
    Coordina la detección (Reader) y la respuesta táctica (Cloner).
    """
    def __init__(self):
        super().__init__("RFID-System")
        self.reader = ReaderEngine()
        self.cloner = RFIDCloner() # Se suscribe al EventBus internamente

    def run(self):
        self.is_running = True
        self.log_event("Sistema RFID Integral Iniciado", level="INFO")
        
        # Iniciamos el hilo del lector
        self.reader.start()

        while self.is_running:
            # Aquí podrías añadir lógica de supervisión o 
            # cambiar modos entre 'Solo Detección' y 'Auto-Clonado'
            import time
            time.sleep(1)

    def stop(self):
        self.reader.stop()
        super().stop()