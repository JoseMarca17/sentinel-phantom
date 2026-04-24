import spidev
import RPi.GPIO as GPIO
import time
from core.logger import get_logger
from core.event_bus import event_bus
from config import config

logger = get_logger('nrf24.scanner')

# Canales 2.4GHz que usan los drones comunes
DRONE_CHANNELS = list(range(0, 126, 5))

# Firmas RF de drones conocidos (por patrón de canal)
DRONE_SIGNATURES = {
    'DJI':      [36, 40, 44, 48],
    'Syma':     [70, 75, 80],
    'Hubsan':   [6, 46, 86],
    'Generic':  list(range(0, 80, 10))
}

class NRF24Scanner:
    def __init__(self):
        self.ce_pin  = config.NRF24_CE_PIN
        self.csn_pin = config.NRF24_CSN_PIN
        self.spi     = None
        self._active_channels = {}
        self._setup()

    def _setup(self) -> None:
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.ce_pin, GPIO.OUT)
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)
            self.spi.max_speed_hz = 10000000
            self._init_nrf24()
            logger.info("nRF24L01 inicializado")
        except Exception as e:
            logger.error(f"nRF24 no disponible: {e}")

    def _init_nrf24(self) -> None:
        self._write_register(0x00, 0x0B)  # CONFIG: PWR_UP, PRX
        self._write_register(0x01, 0x00)  # EN_AA: desactivar auto-ack
        self._write_register(0x02, 0x01)  # EN_RXADDR: pipe 0
        self._write_register(0x03, 0x03)  # SETUP_AW: 5 bytes addr
        self._write_register(0x06, 0x07)  # RF_SETUP: 1Mbps, 0dBm
        time.sleep(0.005)

    def scan_channels(self, duration: float = 5.0) -> dict:
        if not self.spi:
            return {}

        logger.info(f"Escaneando canales nRF24 por {duration}s")
        hits = {ch: 0 for ch in DRONE_CHANNELS}
        end  = time.time() + duration

        while time.time() < end:
            for channel in DRONE_CHANNELS:
                self._set_channel(channel)
                time.sleep(0.0005)
                if self._carrier_detect():
                    hits[channel] += 1

        active = {ch: count for ch, count in hits.items() if count > 0}
        self._active_channels = active

        if active:
            drone_type = self._fingerprint(list(active.keys()))
            logger.info(f"Señales detectadas: {active} | Tipo: {drone_type}")
            event_bus.publish('nrf24.signal_detected', {
                'channels':   active,
                'drone_type': drone_type,
                'severity':   'medium'
            })

        return active

    def _fingerprint(self, active: list[int]) -> str:
        for dtype, signature in DRONE_SIGNATURES.items():
            matches = sum(1 for ch in signature if ch in active)
            if matches >= 2:
                return dtype
        return 'Unknown'

    def _set_channel(self, channel: int) -> None:
        self._write_register(0x05, channel & 0x7F)

    def _carrier_detect(self) -> bool:
        status = self._read_register(0x09)
        return bool(status & 0x01)

    def _write_register(self, reg: int, value: int) -> None:
        GPIO.output(self.ce_pin, GPIO.LOW)
        self.spi.xfer2([0x20 | reg, value])

    def _read_register(self, reg: int) -> int:
        GPIO.output(self.ce_pin, GPIO.LOW)
        resp = self.spi.xfer2([reg, 0x00])
        return resp[1]

    def get_active_channels(self) -> dict:
        return self._active_channels

    def is_available(self) -> bool:
        return self.spi is not None