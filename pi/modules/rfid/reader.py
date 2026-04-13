import board
import busio
from adafruit_pn532.i2c import PN532_I2C
from core.logger import get_logger
from core.event_bus import event_bus

logger = get_logger('rfid.reader')

class RFIDReader:
    def __init__(self):
        self.pn532  = None
        self._setup()

    def _setup(self) -> None:
        try:
            i2c        = busio.I2C(board.SCL, board.SDA)
            self.pn532 = PN532_I2C(i2c, debug=False)
            self.pn532.SAM_configuration()
            fw = self.pn532.firmware_version
            logger.info(f"PN532 listo — FW: {fw[1]}.{fw[2]}")
        except Exception as e:
            logger.error(f"PN532 no disponible: {e}")

    def read_uid(self, timeout: float = 1.0) -> bytes | None:
        if not self.pn532:
            return None
        try:
            uid = self.pn532.read_passive_target(timeout=timeout)
            if uid:
                hex_uid = uid.hex().upper()
                logger.info(f"UID leído: {hex_uid}")
                event_bus.publish('rfid.uid_read', {
                    'uid':  hex_uid,
                    'raw':  list(uid),
                    'type': 'MIFARE_CLASSIC'
                })
            return uid
        except Exception as e:
            logger.error(f"Error leyendo UID: {e}")
            return None

    def read_block(self, block_number: int, key: bytes = b'\xFF\xFF\xFF\xFF\xFF\xFF') -> bytes | None:
        if not self.pn532:
            return None
        try:
            uid = self.read_uid(timeout=0.5)
            if not uid:
                return None
            authenticated = self.pn532.mifare_classic_authenticate_block(
                uid, block_number, 0x60, key
            )
            if not authenticated:
                logger.warning(f"Auth fallida bloque {block_number}")
                return None
            data = self.pn532.mifare_classic_read_block(block_number)
            logger.debug(f"Bloque {block_number}: {data.hex()}")
            return data
        except Exception as e:
            logger.error(f"Error leyendo bloque {block_number}: {e}")
            return None

    def dump_card(self, key: bytes = b'\xFF\xFF\xFF\xFF\xFF\xFF') -> dict:
        """Lee todos los bloques accesibles de una tarjeta MIFARE Classic 1K."""
        blocks = {}
        for block in range(64):
            data = self.read_block(block, key)
            if data:
                blocks[block] = data.hex()
        logger.info(f"Dump completo: {len(blocks)} bloques leídos")
        event_bus.publish('rfid.dump_complete', {'blocks': blocks})
        return blocks

    def is_available(self) -> bool:
        return self.pn532 is not None