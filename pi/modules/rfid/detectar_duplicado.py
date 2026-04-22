import hashlib
from core.logger import get_logger

log = get_logger("module.rfid.defense")

class RFIDDefense:
    def __init__(self, secret_salt="PHANTOM_2026"):
        self.secret_salt = secret_salt

    def generate_signature(self, uid):
        """Genera el hash esperado para el Bloque 4."""
        uid = uid.upper().strip()
        hash_obj = hashlib.sha256((uid + self.secret_salt).encode())
        return hash_obj.hexdigest()[:16].upper()

    def analyze(self, uid, source, block_data=""):
        """Decide si la tarjeta es un clon o es original."""
        threats = []
        if source == "PN532":
            expected = self.generate_signature(uid)
            actual = block_data.strip() if block_data else ""
            
            if actual != expected:
                threats.append({
                    "type": "INVALID_SIGNATURE",
                    "severity": "CRITICAL",
                    "description": "Firma digital no coincide. Posible clon."
                })
        return threats
