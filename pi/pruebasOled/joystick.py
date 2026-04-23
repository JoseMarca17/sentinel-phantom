import time
import threading
import RPi.GPIO as GPIO
import busio
import board
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_ads1x15.ads1x15 import Pin


class JoystickADS1115:
    def __init__(self, event_bus, oled_display=None,
                 btn_pin=17,
                 deadzone=2000,
                 threshold=8000):

        self.bus = event_bus
        self.oled = oled_display

        # ---- GPIO (button) ----
        self.btn_pin = btn_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # ---- I2C / ADS1115 ----
        i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(i2c)

        self.x = AnalogIn(self.ads, Pin.A0)
        self.y = AnalogIn(self.ads, Pin.A1)

        # ---- tuning ----
        self.deadzone = deadzone
        self.threshold = threshold

        self._last_press = {}
        self._running = True

        self._thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name="joystick-ads1115"
        )
        self._thread.start()

    # -------------------------
    # MAIN LOOP
    # -------------------------
    def _poll_loop(self):
        while self._running:
            x_val = self.x.value
            y_val = self.y.value
            btn_pressed = not GPIO.input(self.btn_pin)

            direction = self._get_direction(x_val, y_val)

            if direction:
                self._debounced_press(direction)

            if btn_pressed:
                self._debounced_press("select")

            time.sleep(0.05)

    # -------------------------
    # DIRECTION LOGIC
    # -------------------------
    def _get_direction(self, x, y):
        center_x = 16000
        center_y = 16000

        dx = x - center_x
        dy = y - center_y

        # Ignore small movement (deadzone)
        if abs(dx) < self.deadzone and abs(dy) < self.deadzone:
            return None

        # Ignore diagonals
        if abs(dx) > self.threshold and abs(dy) > self.threshold:
            return None

        if abs(dx) > abs(dy):
            if dx > self.threshold:
                return "right"
            elif dx < -self.threshold:
                return "left"
        else:
            if dy > self.threshold:
                return "down"
            elif dy < -self.threshold:
                return "up"

        return None

    # -------------------------
    # DEBOUNCE
    # -------------------------
    def _debounced_press(self, btn):
        now = time.time()
        if btn not in self._last_press or now - self._last_press[btn] > 0.3:
            self._last_press[btn] = now
            self._handle(btn)

    # -------------------------
    # HANDLE EVENTS (YOUR LOGIC)
    # -------------------------
    def _handle(self, btn: str):
        if self.oled:
            if btn == "up":
                self.oled.nav_up()
            elif btn == "down":
                self.oled.nav_down()
            elif btn == "select":
                if self.oled.active_mod:
                    self.oled.stop_running()
                else:
                    self.oled.nav_select()
            elif btn == "left":
                self.oled.nav_back()
            elif btn == "power":
                self.bus.publish("btn:power", {})

        self.bus.publish(f"btn:{btn}", {"source": "joystick"})
