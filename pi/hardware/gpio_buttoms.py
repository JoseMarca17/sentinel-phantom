import RPi.GPIO as GPIO
import threading
import time
from core.logger import get_logger
from core.event_bus import event_bus

logger = get_logger('gpio_buttons')

# Pines BCM — ajustá según tu cableado
BUTTON_PINS = {
    'up':     17,
    'down':   27,
    'select': 22,
    'back':   23,
}

DEBOUNCE_MS = 200

class GPIOButtons:
    def __init__(self):
        self._setup_gpio()

    def _setup_gpio(self) -> None:
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            for name, pin in BUTTON_PINS.items():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(
                    pin,
                    GPIO.FALLING,
                    callback=self._make_callback(name),
                    bouncetime=DEBOUNCE_MS
                )
            logger.info(f"GPIO botones inicializados: {list(BUTTON_PINS.keys())}")
        except Exception as e:
            logger.error(f"GPIO no disponible: {e}")

    def _make_callback(self, button_name: str):
        def callback(channel):
            logger.debug(f"Botón presionado: {button_name}")
            event_bus.publish('button.pressed', {'button': button_name})
        return callback

    def cleanup(self) -> None:
        GPIO.cleanup()
        logger.info("GPIO liberado")


gpio_buttons = GPIOButtons()