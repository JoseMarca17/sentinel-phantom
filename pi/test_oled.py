import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

oled.contrast(255)
oled.fill(0)
oled.show()

img = Image.new('1', (128, 64))
draw = ImageDraw.Draw(img)
draw.text((0, 0),  "CENTINELA MK1", fill=255)
draw.text((0, 20), "OLED OK",        fill=255)
draw.rectangle((0, 40, 128, 64), fill=255)  # barra solida

oled.image(img)
oled.show()

print("Listo — revisa la pantalla")
