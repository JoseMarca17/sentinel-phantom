import math
from core.logger import get_logger
from core.event_bus import event_bus

logger = get_logger('nrf24.triangulator')

class NRF24Triangulator:
    """
    Triangulación básica por RSSI entre 2 módulos nRF24.
    Requiere que los módulos reporten su RSSI via eventos.
    """
    def __init__(self):
        self._readings = {}
        event_bus.subscribe('nrf24.rssi_reading', self._on_rssi)

    def _on_rssi(self, data: dict) -> None:
        module_id = data.get('module_id', 'A')
        self._readings[module_id] = {
            'rssi':     data.get('rssi', -100),
            'channels': data.get('channels', [])
        }
        if len(self._readings) >= 2:
            self._estimate_position()

    def _estimate_position(self) -> None:
        readings = list(self._readings.values())
        dist_a   = self._rssi_to_distance(readings[0]['rssi'])
        dist_b   = self._rssi_to_distance(readings[1]['rssi'])

        # Estimación relativa simplificada
        total  = dist_a + dist_b
        ratio  = dist_a / total if total > 0 else 0.5

        logger.info(f"Triangulación — dist_A={dist_a:.1f}m dist_B={dist_b:.1f}m ratio={ratio:.2f}")
        event_bus.publish('nrf24.triangulation', {
            'dist_a':  round(dist_a, 2),
            'dist_b':  round(dist_b, 2),
            'ratio':   round(ratio, 2),
            'note':    'Posición relativa estimada entre módulos A y B'
        })

    def _rssi_to_distance(self, rssi: int, tx_power: int = -20, path_loss: float = 2.5) -> float:
        """Modelo log-distance para estimación de distancia por RSSI."""
        if rssi == 0:
            return -1.0
        return round(10 ** ((tx_power - rssi) / (10 * path_loss)), 2)