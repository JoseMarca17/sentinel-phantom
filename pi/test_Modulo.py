import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_ads1x15.ads1x15 import Pin
# Create I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create ADS object
ads = ADS.ADS1115(i2c)

# Create single-ended input on channel 0
chan = AnalogIn(ads, Pin.A0)

print("Reading ADS1115 values, press Ctrl+C to quit...")

while True:
    print("Raw Value: {:>5} | Voltage: {:.3f} V".format(chan.value, chan.voltage))
    time.sleep(0.5)
