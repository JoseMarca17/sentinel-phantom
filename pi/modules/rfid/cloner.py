import time
from core.logger import get_logger

log = get_logger("module.rfid.cloner")

class RFIDCloner:
    def __init__(self, reader):
        self.reader = reader
        self.captured_data = None

    def capture_source(self, timeout=10.0):
        log.info(f"Esperando tarjeta ORIGEN ({timeout}s)...")
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            res = self.reader.read_once()
            if res:
                uid = res['uid']
                # Leemos el secreto del bloque 4
                resp = self.reader.send_command("READ 4")
                if resp and resp.get("event") == "READ_OK":
                    self.captured_data = resp.get("content", "")
                    log.info(f"Secreto capturado de {uid}: {self.captured_data}")
                    return {"status": "SUCCESS", "data": self.captured_data}
            time.sleep(0.1)
        return {"status": "TIMEOUT", "msg": "No se detectó origen"}

    def write_to_destination(self, timeout=10.0):
        if not self.captured_data:
            return {"status": "ERROR", "msg": "No hay datos para clonar"}
        
        log.info(f"Esperando DESTINO para inyectar secreto: {self.captured_data}...")
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            res = self.reader.read_once()
            if res:
                # Escribimos el secreto robado en la nueva tarjeta
                resp = self.reader.send_command(f"WRITE 4 {self.captured_data}")
                if resp and resp.get("event") == "WRITE_OK":
                    log.info("✅ Secreto inyectado con éxito.")
                    return {"status": "SUCCESS", "msg": "Clonado de datos exitoso"}
            time.sleep(0.1)
        return {"status": "TIMEOUT", "msg": "No se detectó destino"}

    def full_clone_flow(self):
        res_source = self.capture_source()
        if res_source["status"] != "SUCCESS": return res_source
        
        log.info("¡Datos robados! CAMBIA LA TARJETA AHORA (3s)...")
        time.sleep(3)
        
        return self.write_to_destination()
