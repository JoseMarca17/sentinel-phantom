import asyncio
from core.base_module import BaseModule
from core.logger import get_logger
from core.event_bus import bus

from modules.bluethooth.scanner import BLEScanner

log = get_logger("module.bluetooth")


class BluetoothModule(BaseModule):

    def __init__(self):
        super().__init__("bluetooth", enabled=True)
        self.scanner   = None
        self._scanning = False

    async def _setup(self):
        self.scanner = BLEScanner()
        log.info("Bluetooth listo ✓")
        bus.publish_sync("oled:bt_status", {"msg": "BT listo"})

    async def _run(self):
        while not self._stop_event.is_set():
            await asyncio.sleep(1)

    async def _teardown(self):
        log.info("Bluetooth detenido")

    async def run_scan(self, duration=10):
        if self._scanning:
            log.warning("Ya hay un escaneo en curso")
            return

        self._scanning = True
        self.scanner.devices_found = []

        bus.publish_sync("oled:bt_status", {"msg": "Escaneando..."})
        log.info("Iniciando escaneo BLE")

        try:
            # El scan de bleak es async pero necesita su propio loop
            # porque no puede correr en el loop principal — va al executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._run_scan_sync, duration)

            devices = self.scanner.devices_found
            log.info(f"{len(devices)} dispositivo(s) encontrado(s)")

            if not devices:
                bus.publish_sync("oled:bt_status", {"msg": "Sin dispositivos"})
                await asyncio.sleep(2)
                return

            # Mostrar conteo
            bus.publish_sync("oled:bt_status", {
                "msg": f"{len(devices)} encontrados"
            })
            await asyncio.sleep(1.5)

            # Mostrar cada dispositivo 2 segundos en pantalla
            for i, d in enumerate(devices):
                nombre = (d.name or "Desconocido")[:14]
                vendor = self.scanner.get_vendor(d.address)[:14]
                mac    = d.address[-8:]

                log.info(f"Mostrando {i+1}/{len(devices)}: {nombre}")

                bus.publish_sync("oled:bt_device", {
                    "index":  i + 1,
                    "total":  len(devices),
                    "name":   nombre,
                    "vendor": vendor,
                    "mac":    mac,
                })
                await asyncio.sleep(2)

        except Exception as e:
            log.error(f"Error en escaneo BLE: {e}")
            bus.publish_sync("oled:bt_status", {"msg": "ERROR BLE"})
            await asyncio.sleep(2)

        finally:
            self._scanning = False
            bus.publish_sync("oled:return_menu", {})

    def _run_scan_sync(self, duration: int):
        """
        Wrapper síncrono para correr el scan async de bleak en un
        thread separado con su propio event loop — obligatorio porque
        bleak no puede correr en el loop principal de asyncio.
        """
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.scanner.scan(duration))
        finally:
            loop.close()