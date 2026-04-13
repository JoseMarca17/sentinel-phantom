import time
from core.logger import get_logger
from core.event_bus import event_bus

logger = get_logger('rfid.cloner')

class RFIDCloner:
    def __init__(self, reader):
        self.reader = reader

    def clone(self, source_blocks: dict, key: bytes = b'\xFF\xFF\xFF\xFF\xFF\xFF') -> bool:
        """
        Escribe los bloques leídos en una tarjeta destino.
        Bloques de sector trailer (3, 7, 11...) se saltan para no brickear.
        """
        if not self.reader.pn532:
            logger.error("PN532 no disponible para clonado")
            return False

        start = time.time()
        written = 0
        failed  = 0

        uid = self.reader.read_uid(timeout=2.0)
        if not uid:
            logger.error("No se detectó tarjeta destino")
            return False

        for block_num, hex_data in source_blocks.items():
            block_num = int(block_num)

            # Saltar sector trailers
            if (block_num + 1) % 4 == 0:
                logger.debug(f"Saltando sector trailer bloque {block_num}")
                continue

            try:
                data = bytes.fromhex(hex_data)
                auth = self.reader.pn532.mifare_classic_authenticate_block(
                    uid, block_num, 0x60, key
                )
                if not auth:
                    logger.warning(f"Auth fallida en bloque {block_num}, saltando")
                    failed += 1
                    continue

                self.reader.pn532.mifare_classic_write_block(block_num, data)
                written += 1
                logger.debug(f"Bloque {block_num} escrito OK")
            except Exception as e:
                logger.error(f"Error escribiendo bloque {block_num}: {e}")
                failed += 1

        elapsed = round(time.time() - start, 2)
        success = failed == 0

        event_bus.publish('rfid.clone_complete', {
            'written': written,
            'failed':  failed,
            'elapsed': elapsed,
            'success': success
        })
        logger.info(f"Clonado: {written} OK, {failed} errores, {elapsed}s")
        return success