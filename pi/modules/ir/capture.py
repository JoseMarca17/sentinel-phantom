from core.logger import get_logger
from core.event_bus import event_bus
from hardware.pico_bridge import pico

logger = get_logger('ir.capture')

class IRCapture:
    def __init__(self):
        self._last_signal = None
        event_bus.subscribe('pico.ir_captured', self._on_captured)

    def start_capture(self) -> bool:
        logger.info("Iniciando captura IR en Pico W")
        result = pico.send('ir_capture_start')
        return result

    def stop_capture(self) -> bool:
        return pico.send('ir_capture_stop')

    def _on_captured(self, data: dict) -> None:
        self._last_signal = data
        logger.info(f"Señal IR capturada: {data.get('protocol', 'RAW')} {data.get('code', '')}")
        event_bus.publish('ir.signal_captured', {
            'protocol': data.get('protocol', 'RAW'),
            'code':     data.get('code', ''),
            'raw':      data.get('raw', []),
            'length':   data.get('length', 0)
        })

    def get_last(self) -> dict | None:
        return self._last_signal