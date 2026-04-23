import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_ads1x15.ads1x15 import Pin  # 👈 ESTE ES EL QUE TE SALVA

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

x = AnalogIn(ads, Pin.A0)
y = AnalogIn(ads, Pin.A1)

while True:
    print("X:", x.value, "Y:", y.value)
    time.sleep(0.3)