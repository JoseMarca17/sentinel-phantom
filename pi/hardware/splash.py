"""
splash.py  —  Pantalla de carga SENTINEL PHANTOM
Compatible con OledDisplay (adafruit_ssd1306 + PIL)

Uso:
    from splash import run_splash

    # En OledDisplay reemplaza show_boot:
    def show_boot(self):
        run_splash(self)
"""

import time
from PIL import Image, ImageDraw

W, H = 128, 64

# ──────────────────────────────────────────────────────────
#  FUENTE DOOM GRUESA  6 cols × 8 rows
#  Cada '1' se dibuja como un bloque de sc×sc píxeles
#  Con sc=2 en 128×64: cada letra ≈ 12×16 px → bien gruesa
# ──────────────────────────────────────────────────────────
DOOM = {
    'A': ["011110","110011","110011","111111","110011","110011","110011","000000"],
    'B': ["111110","110011","110011","111110","110011","110011","111110","000000"],
    'C': ["011110","110011","110000","110000","110000","110011","011110","000000"],
    'D': ["111100","110011","110011","110011","110011","110011","111100","000000"],
    'E': ["111111","110000","110000","111110","110000","110000","111111","000000"],
    'F': ["111111","110000","110000","111110","110000","110000","110000","000000"],
    'G': ["011110","110000","110000","110111","110011","110011","011110","000000"],
    'H': ["110011","110011","110011","111111","110011","110011","110011","000000"],
    'I': ["011110","001100","001100","001100","001100","001100","011110","000000"],
    'K': ["110011","110110","111100","111000","111100","110110","110011","000000"],
    'L': ["110000","110000","110000","110000","110000","110000","111111","000000"],
    'M': ["110011","111111","111111","110011","110011","110011","110011","000000"],
    'N': ["110011","111011","110111","110011","110011","110011","110011","000000"],
    'O': ["011110","110011","110011","110011","110011","110011","011110","000000"],
    'P': ["111110","110011","110011","111110","110000","110000","110000","000000"],
    'R': ["111110","110011","110011","111110","111000","110110","110011","000000"],
    'S': ["011110","110011","110000","011110","000111","110011","011110","000000"],
    'T': ["111111","001100","001100","001100","001100","001100","001100","000000"],
    'U': ["110011","110011","110011","110011","110011","110011","011110","000000"],
    'V': ["110011","110011","110011","110011","011110","011110","001100","000000"],
    'W': ["110011","110011","110011","111111","111111","110011","110011","000000"],
    'X': ["110011","011110","011110","001100","011110","011110","110011","000000"],
    'Y': ["110011","110011","011110","001100","001100","001100","001100","000000"],
    'Z': ["111111","000011","000110","001100","011000","110000","111111","000000"],
    ' ': ["000000","000000","000000","000000","000000","000000","000000","000000"],
    '>': ["110000","011000","001100","000110","001100","011000","110000","000000"],
}

COLS = 6
ROWS = 8


def _cw(sc):
    """Ancho de un carácter + kerning."""
    return COLS * sc + max(1, sc // 2)


def _sw(text, sc):
    return len(text) * _cw(sc) - max(1, sc // 2)


def _center_x(text, sc):
    return max(0, (W - _sw(text, sc)) // 2)


def _draw_char(draw, ch, ox, oy, sc):
    g = DOOM.get(ch.upper(), DOOM[' '])
    for r, row in enumerate(g):
        for c, bit in enumerate(row):
            if bit == '1':
                x0 = ox + c * sc
                y0 = oy + r * sc
                draw.rectangle([x0, y0, x0 + sc - 1, y0 + sc - 1], fill=255)


def _draw_str(draw, text, ox, oy, sc):
    x = ox
    for ch in text.upper():
        _draw_char(draw, ch, x, oy, sc)
        x += _cw(sc)


# ──────────────────────────────────────────────────────────
#  FUNCIÓN PRINCIPAL
# ──────────────────────────────────────────────────────────

def run_splash(oled):
    """
    Pantalla de carga animada para SENTINEL PHANTOM.
    Secuencia:
        1. "SENTINEL" aparece letra a letra (centrado)
        2. "PHANTOM"  aparece letra a letra (centrado)
        3. Muros blancos se cierran desde los lados
        4. Muros se abren revelando el menú
    """
    draw   = oled.draw
    image  = oled.image
    lock   = oled.lock
    device = oled.device

    def _push():
        device.image(image)
        device.show()

    def _clear():
        draw.rectangle((0, 0, W - 1, H - 1), fill=0)

    # ── Escala del logo ──────────────────────────────────
    # sc=2 → cada dot = 2×2 px → letra 12×16 px
    # SENTINEL (8 letras) → ≈ 104 px → cabe en 128 px
    sc = 2
    char_h = ROWS * sc
    gap    = 2
    L1, L2 = "SENTINEL", "PHANTOM"

    total_h = char_h * 2 + gap
    y1 = (H - total_h) // 2
    y2 = y1 + char_h + gap

    # ── Fase 1: Logo letra a letra ───────────────────────
    with lock:
        _clear()
        _push()
    time.sleep(0.08)

    x = _center_x(L1, sc)
    for ch in L1:
        with lock:
            _draw_char(draw, ch, x, y1, sc)
            _push()
        x += _cw(sc)
        time.sleep(0.07)

    x = _center_x(L2, sc)
    for ch in L2:
        with lock:
            _draw_char(draw, ch, x, y2, sc)
            _push()
        x += _cw(sc)
        time.sleep(0.07)

    time.sleep(0.6)

    # ── Fase 2: Snapshot del logo ────────────────────────
    logo_snap = image.copy()

    # ── Fase 3: Muros se cierran ─────────────────────────
    for wall in range(0, W // 2 + 2, 2):
        with lock:
            image.paste(logo_snap)
            draw.rectangle([0, 0, wall, H - 1], fill=255)
            draw.rectangle([W - 1 - wall, 0, W - 1, H - 1], fill=255)
            _push()
        time.sleep(0.012)

    with lock:
        draw.rectangle([0, 0, W - 1, H - 1], fill=255)
        _push()
    time.sleep(0.16)

    # ── Fase 4: Pre-render menú ──────────────────────────
    menu_img  = Image.new("1", (W, H))
    menu_draw = ImageDraw.Draw(menu_img)

    items   = ["DEFENSA", "ATAQUE", "ESTADO"]
    msc     = 1                    # 1px por dot en OLED real
    line_h  = ROWS * msc + 2
    start_y = (H - len(items) * line_h) // 2

    for i, item in enumerate(items):
        prefix = ">" if i == 0 else " "
        _draw_str(menu_draw, prefix + " " + item, 1, start_y + i * line_h, msc)

    # ── Fase 5: Muros se abren ───────────────────────────
    for wall in range(W // 2 + 2, -1, -2):
        with lock:
            image.paste(menu_img)
            if wall > 0:
                draw.rectangle([0, 0, wall, H - 1], fill=255)
                draw.rectangle([W - 1 - wall, 0, W - 1, H - 1], fill=255)
            _push()
        time.sleep(0.012)

    with lock:
        image.paste(menu_img)
        _push()

    time.sleep(0.1)