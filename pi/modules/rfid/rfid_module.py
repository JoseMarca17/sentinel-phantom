import asyncio
from core.base_module import BaseModule
from core.logger import get_logger
from core.event_bus import bus

from modules.rfid.reader import RFIDReader
from modules.rfid.cloner import RFIDCloner

log = get_logger("module.rfid")


class RFIDModule(BaseModule):

    def __init__(self):
        super().__init__("rfid", enabled=True)
        self.reader = None
        self.cloner = None
        self._cloning_event = None

    async def _setup(self):
        self._cloning_event = asyncio.Event()
        self.reader = RFIDReader()
        self.cloner = RFIDCloner(self.reader)

        log.info("RFID listo ✓")
        bus.publish_sync("oled:rfid_status", {"msg": "RFID listo"})

    async def _run(self):
        while not self._stop_event.is_set():

            if self._cloning_event.is_set():
                await asyncio.sleep(0.1)
                continue

            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.reader.read_once
                )

                if self._cloning_event.is_set():
                    await asyncio.sleep(0.1)
                    continue

                if result:
                    uid = result["uid"]
                    log.info(f"UID detectado: {uid}")
                    bus.publish_sync("oled:rfid_status", {
                        "msg": f"UID: {uid[:8]}"
                    })
                    await asyncio.sleep(1)

            except Exception as e:
                log.error(f"RFID error: {e}")

            await asyncio.sleep(0.1)

    async def _teardown(self):
        log.info("RFID detenido")

    async def clone_card(self):
        log.info("clone_card() iniciado")

        self._cloning_event.set()
        await asyncio.sleep(1.5)

        log.info("Cediendo reader al cloner")

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.cloner.full_clone_flow
            )
            log.info(f"Clonado terminado: {result}")
            return result

        except Exception as e:
            log.error(f"clone_card() excepción: {e}")
            raise

        finally:
            self._cloning_event.clear()
            log.info("_cloning_event limpiado, _run retoma control")
            # Notificar al OLED que vuelva al menú anterior
            bus.publish_sync("oled:return_menu", {})