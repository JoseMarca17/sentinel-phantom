import threading
import time
from core.base_module import BaseModule
from modules.tscm.scanner import TSCMScanner

class TSCMModule(BaseModule):
    def __init__(self):
        super().__init__('tscm')
        self.scanner  = TSCMScanner()
        self._running = False
        self._thread  = None
        self.interval = 60  # segundos entre scans

    def _setup(self) -> None:
        self._running = True
        self._thread  = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()
        self.logger.info("TSCM module listo")

    def _teardown(self) -> None:
        self._running = False

    def _scan_loop(self) -> None:
        while self._running:
            try:
                self.scanner.scan()
            except Exception as e:
                self.logger.error(f"Error en scan loop TSCM: {e}")
            time.sleep(self.interval)

    def scan_now(self) -> list[dict]:
        return self.scanner.scan()

    def get_status(self) -> dict:
        return {
            'module':   self.name,
            'status':   self.status.value,
            'devices':  len(self.scanner.get_devices()),
            'interval': self.interval,
            'scanning': self._running
        }