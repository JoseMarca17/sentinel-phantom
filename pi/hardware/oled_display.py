from config import DEBUG_MODE

class OLEDDriver:
    def __init__(self):
        self.device = None
        if DEBUG_MODE:
            from luma.emulator.device import pygame
            self.device = pygame(width=128, height=64)
        else:
            from luma.oled.device import ssd1306
            from luma.core.interface.serial import i2c
            serial = i2c(port=1, address=0x3C)
            self.device = ssd1306(serial)

    def show_text(self, line1, line2=""):
        from luma.core.render import canvas
        with canvas(self.device) as draw:
            draw.text((10, 20), line1, fill="white")
            draw.text((10, 40), line2, fill="white")