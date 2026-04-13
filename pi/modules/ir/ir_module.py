from core.base_module import BaseModule
from modules.ir.capture import IRCapture
from modules.ir.replay import IRReplay

class IRModule(BaseModule):
    def __init__(self):
        super().__init__('ir')
        self.capture = IRCapture()
        self.replay  = IRReplay()

    def _setup(self) -> None:
        from hardware.pico_bridge import pico
        if not pico.is_connected():
            raise RuntimeError("Pico W no conectado")
        self.logger.info("IR module listo")

    def _teardown(self) -> None:
        self.capture.stop_capture()

    def get_status(self) -> dict:
        return {
            'module':      self.name,
            'status':      self.status.value,
            'last_signal': self.capture.get_last()
        }