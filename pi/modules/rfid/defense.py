import time
import hashlib
from collections import defaultdict
from core.logger import get_logger

log = get_logger("module.rfid.defense")

class RFIDDefense:
    """
    Motor de Seguridad de CENTINEL PHANTOM
    Maneja: Anti-clonado, Firmas Digitales y Whitelist.
    """

    def __init__(self, secret_salt="PHANTOM_EMI_2026_PRO"):
        self.secret_salt = secret_salt
        self._scan_history = defaultdict(list) # uid -> [{'ts': float, 'src': str}]
        self._whitelist = set() # Puedes cargar esto de la DB después
        
        # Parámetros de seguridad
        self.CLONE_WINDOW = 5.0  # Segundos para detectar duplicidad física
        self.MAX_SAMPLES = 5     # Cantidad de lecturas a recordar por UID

    def analyze(self, uid: str, source: str, block_data: str = "") -> list[dict]:
        """
        Analiza un escaneo en busca de amenazas.
        Retorna una lista de dicts con las amenazas encontradas.
        """
        threats = []
        uid = uid.upper()
        now = time.time()

        # 1. DETECCIÓN DE DUPLICIDAD FÍSICA (Anti-Spoofing)
        if uid in self._scan_history:
            last_entry = self._scan_history[uid][-1]
            diff = now - last_entry['ts']
            
            # Si aparece en OTRA fuente demasiado rápido
            if source != last_entry['src'] and diff < self.CLONE_WINDOW:
                threats.append({
                    "type": "PHYSICAL_DUPLICATION",
                    "severity": "HIGH",
                    "description": f"UID detectado en {last_entry['src']} y {source} en {diff:.2f}s. Imposible físicamente."
                })

        # 2. VERIFICACIÓN DE FIRMA SECRETA (Integridad de Memoria)
        if block_data:
            expected_sig = self.generate_signature(uid)
            if block_data != expected_sig:
                threats.append({
                    "type": "INVALID_SIGNATURE",
                    "severity": "CRITICAL",
                    "description": "El UID es válido pero la firma digital en memoria es FALSA o está ausente."
                })
        else:
            # Si el sistema esperaba datos y no llegaron
            threats.append({
                "type": "MISSING_DATA_PAYLOAD",
                "severity": "MEDIUM",
                "description": "Intento de acceso con UID puro (sin verificación de bloques de datos)."
            })

        # Actualizar historial
        self._scan_history[uid].append({'ts': now, 'src': source})
        if len(self._scan_history[uid]) > self.MAX_SAMPLES:
            self._scan_history[uid].pop(0)

        return threats

    def generate_signature(self, uid: str) -> str:
        """Genera la firma que debería tener el Bloque 4."""
        hash_obj = hashlib.sha256((uid + self.secret_salt).encode())
        return hash_obj.hexdigest()[:16].upper()

    def is_authorized(self, uid: str) -> bool:
        """Consulta rápida a la whitelist."""
        return uid.upper() in self._whitelist

    def add_to_whitelist(self, uid: str):
        self._whitelist.add(uid.upper())
