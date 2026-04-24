# import time
# import threading
# import RPi.GPIO as GPIO
# import busio
# import board
# import adafruit_ads1x15.ads1115 as ADS
# from adafruit_ads1x15.analog_in import AnalogIn
# from adafruit_ads1x15.ads1x15 import Pin
# import logging

# logger = logging.getLogger(__name__)


# class JoystickADS1115:
#     def __init__(self, event_bus, i2c_lock=None,
#                  btn_pin=17,
#                  deadzone=2000,
#                  threshold=8000):

#         self.bus = event_bus
#         self._lock = i2c_lock or threading.Lock()
#         print("JOY LOCK:", id(self._lock))
#         GPIO.setmode(GPIO.BCM)
#         GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#         self.btn_pin = btn_pin

#         i2c_bus = busio.I2C(board.SCL, board.SDA)
#         self.ads = ADS.ADS1115(i2c_bus)

#         self.x = AnalogIn(self.ads, Pin.A0)
#         self.y = AnalogIn(self.ads, Pin.A1)

#         self.deadzone = deadzone
#         self.threshold = threshold

#         self._running = True
#         self._consecutive_errors = 0
#         self._MAX_ERRORS = 5

#         threading.Thread(target=self._poll_loop, daemon=True).start()

#     def _poll_loop(self):
#         while self._running:
#             try:
#                 with self._lock:
#                     x_val = self.x.value
#                     y_val = self.y.value

#                 # Reset error counter si la lectura fue exitosa
#                 self._consecutive_errors = 0

#                 btn_pressed = not GPIO.input(self.btn_pin)
#                 direction = self._get_direction(x_val, y_val)

#                 if direction:
#                     self._publish(direction)

#                 if btn_pressed:
#                     self._publish("select")

#             except OSError as e:
#                 self._consecutive_errors += 1
#                 logger.warning(
#                     f"[Joystick] Error I2C (intento {self._consecutive_errors}): {e}"
#                 )

#                 if self._consecutive_errors >= self._MAX_ERRORS:
#                     logger.error(
#                         "[Joystick] Demasiados errores I2C consecutivos. "
#                         "Verifica conexiones del ADS1115."
#                     )
#                     # Esperar mas tiempo antes de reintentar
#                     time.sleep(2.0)
#                     self._consecutive_errors = 0
#                 else:
#                     time.sleep(0.2)
#                 continue

#             time.sleep(0.10)

#     def _publish(self, direction):
#         if self.bus:
#             self.bus.publish(f"nav:{direction}", {})

#     def _get_direction(self, x, y):
#         center = 16000
#         dx = x - center
#         dy = y - center

#         if abs(dx) < self.deadzone and abs(dy) < self.deadzone:
#             return None

#         if abs(dx) > abs(dy):
#             return "right" if dx > self.threshold else "left"
#         else:
#             return "down" if dy > self.threshold else "up"

#     def stop(self):
#         self._running = False


# import time
# import threading
# import RPi.GPIO as GPIO
# import busio
# import board
# import adafruit_ads1x15.ads1115 as ADS
# from adafruit_ads1x15.analog_in import AnalogIn
# from adafruit_ads1x15.ads1x15 import Pin
# import logging

# logger = logging.getLogger(__name__)


# class JoystickADS1115:
#     def __init__(self, event_bus, i2c_lock=None, i2c_bus=None,
#                  btn_pin=17,
#                  deadzone=2000,
#                  threshold=8000):

#         self.bus = event_bus
#         self._lock = i2c_lock or threading.Lock()
#         print("JOY LOCK:", id(self._lock))
#         GPIO.setmode(GPIO.BCM)
#         GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#         self.btn_pin = btn_pin

#         # Usar el bus I2C compartido si se provee, o crear uno propio como fallback
#         shared_i2c = i2c_bus or busio.I2C(board.SCL, board.SDA)
#         self.ads = ADS.ADS1115(shared_i2c)

#         self.x = AnalogIn(self.ads, Pin.A0)
#         self.y = AnalogIn(self.ads, Pin.A1)

#         self.deadzone = deadzone
#         self.threshold = threshold

#         self._running = True
#         self._consecutive_errors = 0
#         self._MAX_ERRORS = 5

#         threading.Thread(target=self._poll_loop, daemon=True).start()

#     def _poll_loop(self):
#         while self._running:
#             try:
#                 with self._lock:
#                     x_val = self.x.value
#                     y_val = self.y.value

#                 # Reset error counter si la lectura fue exitosa
#                 self._consecutive_errors = 0

#                 btn_pressed = not GPIO.input(self.btn_pin)
#                 direction = self._get_direction(x_val, y_val)

#                 if direction:
#                     self._publish(direction)

#                 if btn_pressed:
#                     self._publish("select")

#             except OSError as e:
#                 self._consecutive_errors += 1
#                 logger.warning(
#                     f"[Joystick] Error I2C (intento {self._consecutive_errors}): {e}"
#                 )

#                 if self._consecutive_errors >= self._MAX_ERRORS:
#                     logger.error(
#                         "[Joystick] Demasiados errores I2C consecutivos. "
#                         "Verifica conexiones del ADS1115."
#                     )
#                     # Esperar mas tiempo antes de reintentar
#                     time.sleep(2.0)
#                     self._consecutive_errors = 0
#                 else:
#                     time.sleep(0.2)
#                 continue

#             time.sleep(0.10)

#     def _publish(self, direction):
#         if self.bus:
#             self.bus.publish(f"nav:{direction}", {})

#     def _get_direction(self, x, y):
#         center = 16000
#         dx = x - center
#         dy = y - center

#         if abs(dx) < self.deadzone and abs(dy) < self.deadzone:
#             return None

#         if abs(dx) > abs(dy):
#             return "right" if dx > self.threshold else "left"
#         else:
#             return "down" if dy > self.threshold else "up"

#     def stop(self):
#         self._running = False

import time
import threading
import RPi.GPIO as GPIO
import busio
import board
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_ads1x15.ads1x15 import Pin
import logging

logger = logging.getLogger(__name__)


class Joystick:
    def __init__(self, event_bus, i2c_lock, i2c_bus,
                 btn_pin=17,
                 deadzone=1500,
                 threshold=3000):

        self.bus = event_bus
        self._lock = i2c_lock

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.btn_pin = btn_pin

        self.ads = ADS.ADS1115(i2c_bus)

        self.x = AnalogIn(self.ads, Pin.A0)
        self.y = AnalogIn(self.ads, Pin.A1)

        # 🔥 calibración inicial
        time.sleep(0.5)
        self.center_x = self.x.value
        self.center_y = self.y.value

        self.deadzone = deadzone
        self.threshold = threshold

        self._running = True

        threading.Thread(target=self._poll_loop, daemon=True).start()

    def _poll_loop(self):
        while self._running:
            try:
                with self._lock:
                    x_val = self.x.value
                    y_val = self.y.value

                dx = x_val - self.center_x
                dy = y_val - self.center_y

                if abs(dx) < self.deadzone and abs(dy) < self.deadzone:
                    direction = None
                elif abs(dx) > abs(dy):
                    direction = "right" if dx > self.threshold else "left"
                else:
                    direction = "down" if dy > self.threshold else "up"

                if direction:
                    self._publish(direction)

                if not GPIO.input(self.btn_pin):
                    self._publish("select")

            except Exception as e:
                logger.warning(f"[Joystick] Error I2C: {e}")
                time.sleep(0.3)

            time.sleep(0.2)

    def _publish(self, direction):
        if self.bus:
            self.bus.publish_sync(f"nav:{direction}", {})

    def stop(self):
        self._running = False