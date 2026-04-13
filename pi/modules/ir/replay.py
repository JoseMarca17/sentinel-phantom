from core.logger import get_logger
from core.event_bus import event_bus
from hardware.pico_bridge import pico

logger = get_logger('ir.replay')

class IRReplay:
    def replay(self, signal: dict) -> bool:
        if not signal:
            logger.warning("No hay señal IR para reproducir")
            return False

        logger.info(f"Reproduciendo señal IR: {signal.get('protocol')} {signal.get('code')}")
        result = pico.send('ir_replay', {
            'protocol': signal.get('protocol', 'RAW'),
            'code':     signal.get('code', ''),
            'raw':      signal.get('raw', [])
        })
        if result:
            event_bus.publish('ir.signal_replayed', signal)
        return result

    def replay_raw(self, raw_data: list[int]) -> bool:
        return self.replay({'protocol': 'RAW', 'code': '', 'raw': raw_data})