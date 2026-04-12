from config import DEBUG_MODE

class PN532Driver:
    def __init__(self):
        self.adapter = None
        if not DEBUG_MODE:
            # Solo intenta cargar librerías reales en la Raspberry
            from py532.nfc import NfcAdapter
            self.adapter = NfcAdapter()
    
    def read_uid(self):
        """Retorna el UID de la tarjeta detectada."""
        if DEBUG_MODE:
            # Aquí podrías automatizar una respuesta para pruebas
            return None 
        try:
            # Lógica real para capturar en < 5 segundos [cite: 221]
            return self.adapter.scan_field().hex(':').upper()
        except:
            return None