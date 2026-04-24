import time
from core.logger import get_logger
from core.event_bus import bus

log = get_logger("module.rfid.cloner")


class RFIDCloner:
    def __init__(self, reader):
        self.reader = reader
        self.captured_data = None

    # ── Helper para UI ─────────────────────────
    def _emit(self, msg):
        try:
            bus.publish_sync("oled:rfid_status", {"msg": msg})
        except Exception as e:
            log.warning(f"No se pudo emitir evento OLED: {e}")

    # ── CAPTURA ORIGEN ────────────────────────
    def capture_source(self, timeout=15.0):
        self._emit("ACERCA ORIGEN")
        log.info(f"Esperando tarjeta ORIGEN ({timeout}s)...")

        start_time = time.time()

        while (time.time() - start_time) < timeout:
            try:
                res = self.reader.read_once()

                if res:
                    uid = res.get("uid", "????")
                    self._emit(f"UID: {uid[:8]}")
                    log.info(f"UID detectado: {uid}")

                    # Delay crítico: darle tiempo al ESP32 para que termine
                    # su ciclo actual de readPassiveTargetID antes de mandar READ
                    time.sleep(0.5)

                    self._emit("LEYENDO...")
                    resp = self.reader.send_command("READ 4", timeout=4.0)

                    if resp and resp.get("event") == "READ_OK":
                        self.captured_data = resp.get("content", "")
                        self._emit("DATOS OK!")
                        log.info(f"Datos capturados: {self.captured_data}")
                        return {"status": "SUCCESS"}

                    else:
                        # READ falló — puede ser que la tarjeta se movió o es de solo lectura
                        log.warning(f"READ 4 falló: {resp}")
                        self._emit("MANTÉN TARJETA")
                        time.sleep(0.5)

            except Exception as e:
                log.error(f"Error leyendo ORIGEN: {e}")
                self._emit("ERROR LECTURA")

            time.sleep(0.1)

        self._emit("TIMEOUT ORIGEN")
        return {"status": "TIMEOUT"}

    # ── ESCRITURA DESTINO ─────────────────────
    def write_to_destination(self, timeout=15.0):
        if not self.captured_data:
            self._emit("SIN DATOS")
            return {"status": "ERROR"}

        self._emit("ACERCA DESTINO")
        log.info("Esperando tarjeta DESTINO...")

        start_time = time.time()

        while (time.time() - start_time) < timeout:
            try:
                res = self.reader.read_once()

                if res:
                    self._emit("ESCRIBIENDO...")

                    # Mismo delay que en capture para sincronizar con el ESP32
                    time.sleep(0.5)

                    resp = self.reader.send_command(
                        f"WRITE 4 {self.captured_data}",
                        timeout=4.0
                    )

                    if resp and resp.get("event") == "WRITE_OK":
                        self._emit("CLONADO OK!")
                        log.info("Clonado exitoso")
                        return {"status": "SUCCESS"}
                    else:
                        log.warning(f"WRITE falló: {resp}")
                        self._emit("MANTÉN TARJETA")
                        time.sleep(0.5)

            except Exception as e:
                log.error(f"Error en DESTINO: {e}")
                self._emit("ERROR WRITE")

            time.sleep(0.1)

        self._emit("TIMEOUT DEST")
        return {"status": "TIMEOUT"}

    # ── FLUJO COMPLETO ────────────────────────
    def full_clone_flow(self):
        self._emit("INICIANDO...")
        log.info("Iniciando flujo de clonado")

        res = self.capture_source()

        if res["status"] != "SUCCESS":
            self._emit("FALLO ORIGEN")
            return res

        self._emit("CAMBIA TARJETA")

        for i in range(3, 0, -1):
            self._emit(f"LISTO EN {i}...")
            time.sleep(1)

        return self.write_to_destination()