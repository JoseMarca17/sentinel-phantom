import threading
import time
from core.base_module import BaseModule
from modules.nrf24.scanner import NRF24Scanner
from modules.nrf24.triangulator import NRF24Triangulator

class NRF24Module(BaseModule):
    def __init__(self):
        super().__init__('nrf24')
        self.scanner      = NRF24Scanner()
        self.triangulator = NRF24Triangulator()
        self._running     = False
        self._thread      = None
        self.interval     = 10  # segundos entre scans

    def _setup(self) -> None:
        if not self.scanner.is_available():
            raise RuntimeError("nRF24L01 no detectado")
        self._running = True
        self._thread  = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()
        self.logger.info("nRF24 module listo")

    def _teardown(self) -> None:
        self._running = False

    def _scan_loop(self) -> None:
        while self._running:
            try:
                self.scanner.scan_channels(duration=5.0)
            except Exception as e:
                self.logger.error(f"Error en scan loop nRF24: {e}")
            time.sleep(self.interval)

    def scan_now(self) -> dict:
        return self.scanner.scan_channels(duration=5.0)

    def mousejack(self, channel: int) -> bool:
        """
        MouseJack: inyección de paquetes en dispositivos Nordic sin cifrado.
        Requiere que el ESP32 ejecute el ataque real vía UART.
        """
        from hardware.esp32_bridge import esp32
        self.logger.warning(f"MouseJack en canal {channel}")
        return esp32.send('mousejack', {'channel': channel})

    def get_status(self) -> dict:
        return {
            'module':   self.name,
            'status':   self.status.value,
            'active':   self.scanner.get_active_channels(),
            'scanning': self._running
        }