import serial
import json
import threading
from core.logger import get_logger
from core.event_bus import event_bus
from config import config

logger = get_logger('pico_bridge')

class PicoBridge:
    def __init__(self):
        self.port     = config.PICO_PORT
        self.baud     = config.PICO_BAUD
        self.serial   = None
        self._running = False
        self._thread  = None

    def connect(self) -> bool:
        try:
            self.serial = serial.Serial(self.port, self.baud, timeout=1)
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            logger.info(f"Pico W conectado en {self.port}")
            return True
        except Exception as e:
            logger.error(f"No se pudo conectar al Pico W: {e}")
            return False

    def disconnect(self) -> None:
        self._running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
        logger.info("Pico W desconectado")

    def send(self, command: str, payload: dict = None) -> bool:
        if not self.serial or not self.serial.is_open:
            logger.warning("Pico W no conectado, comando ignorado")
            return False
        try:
            msg = json.dumps({'cmd': command, 'data': payload or {}}) + '\n'
            self.serial.write(msg.encode('utf-8'))
            logger.debug(f"Pico W → {msg.strip()}")
            return True
        except Exception as e:
            logger.error(f"Error enviando al Pico W: {e}")
            return False

    def _read_loop(self) -> None:
        while self._running:
            try:
                if self.serial and self.serial.in_waiting:
                    line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self._handle_message(line)
            except Exception as e:
                logger.error(f"Error leyendo Pico W: {e}")
                break

    def _handle_message(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
            event = msg.get('event', 'pico.unknown')
            data  = msg.get('data', {})
            logger.debug(f"Pico W ← {event}: {data}")
            event_bus.publish(f'pico.{event}', data)
        except json.JSONDecodeError:
            logger.warning(f"Pico W mensaje no JSON: {raw}")

    def is_connected(self) -> bool:
        return self.serial is not None and self.serial.is_open


pico = PicoBridge()