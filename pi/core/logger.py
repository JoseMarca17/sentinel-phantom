import logging
from database.local_db import LocalDB

class SentinelLogger:
    def __init__(self):
        self.db = LocalDB()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("SentinelPhantom")

    def log(self, module, level, message):
        # Registro en consola para depuración en tiempo real [cite: 156, 181]
        self.logger.info(f"[{module}] {message}")
        # Registro en SQLite para validación de métricas [cite: 139, 214]
        self.db.insert_log(module, level, message)

# Instancia global
logger = SentinelLogger()