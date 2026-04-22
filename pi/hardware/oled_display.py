import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
from core.logger import get_logger
from config import config

logger = get_logger('oled_display')

WIDTH  = 128
HEIGHT = 64

class OLEDDisplay:
    def __init__(self):
        self.display = None
        self.image   = None
        self.draw    = None
        self._init_display()

    def _init_display(self) -> None:
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.display = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=config.OLED_ADDRESS)
            self.display.fill(0)
            self.display.show()
            self.image = Image.new('1', (WIDTH, HEIGHT))
            self.draw  = ImageDraw.Draw(self.image)
            logger.info("OLED inicializado")
        except Exception as e:
            logger.error(f"OLED no disponible: {e}")

    def clear(self) -> None:
        if not self.display:
            return
        self.draw.rectangle((0, 0, WIDTH, HEIGHT), outline=0, fill=0)
        self._flush()

    def show_text(self, lines: list[str], font_size: int = 10) -> None:
        if not self.display:
            return
        self.clear()
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', font_size)
        except Exception:
            font = ImageFont.load_default()

        y = 0
        for line in lines[:4]:
            self.draw.text((0, y), str(line), font=font, fill=255)
            y += font_size + 2

        self._flush()

    def show_menu(self, title: str, items: list[str], selected: int = 0) -> None:
        if not self.display:
            return
        self.clear()
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)
        except Exception:
            font = ImageFont.load_default()

        # Título con fondo invertido
        self.draw.rectangle((0, 0, WIDTH, 12), outline=255, fill=255)
        self.draw.text((2, 1), title[:18], font=font, fill=0)

        # Items del menú
        for i, item in enumerate(items[:5]):
            y = 14 + i * 10
            prefix = '>' if i == selected else ' '
            self.draw.text((0, y), f"{prefix}{item[:17]}", font=font, fill=255)

        self._flush()

    def show_alert(self, title: str, message: str) -> None:
        self.show_text([f"!! {title} !!", message])

    def _flush(self) -> None:
        if self.display:
            self.display.image(self.image)
            self.display.show()

    def is_available(self) -> bool:
        return self.display is not None

oled = OLEDDisplay()