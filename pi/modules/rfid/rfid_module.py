from core.base_module import BaseModule
from modules.rfid.reader import RFIDReader
from modules.rfid.cloner import RFIDCloner
import threading

class RFIDModule(BaseModule):
    def __init__(self):
        super().__init__('rfid')
        self.reader  = RFIDReader()
        self.cloner  = None
        self._thread = None
        self._scanning = False

    def _setup(self) -> None:
        if not self.reader.is_available():
            raise RuntimeError("PN532 no detectado")
        self.cloner = RFIDCloner(self.reader)
        self.logger.info("RFID module listo")

    def _teardown(self) -> None:
        self._scanning = False

    def start_scan_loop(self) -> None:
        """Escaneo continuo en background."""
        if self._scanning:
            return
        self._scanning = True
        self._thread   = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()

    def stop_scan_loop(self) -> None:
        self._scanning = False

    def _scan_loop(self) -> None:
        self.logger.info("Scan loop RFID iniciado")
        while self._scanning:
            self.reader.read_uid(timeout=0.5)

    def get_status(self) -> dict:
        return {
            'module':    self.name,
            'status':    self.status.value,
            'pn532':     self.reader.is_available(),
            'scanning':  self._scanning
        }