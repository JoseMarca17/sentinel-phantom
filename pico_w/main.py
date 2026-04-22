import machine
import ssd1306
import time

# --- CONFIGURACIÓN DE PINES ---
# I2C: SCL en GP9 (pin 12), SDA en GP8 (pin 11)
i2c = machine.I2C(0, scl=machine.Pin(9), sda=machine.Pin(8))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# JOYSTICK: VRX en GP26, VRY en GP27, SW en GP22
vrx = machine.ADC(machine.Pin(26))
vry = machine.ADC(machine.Pin(27))
sw = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_UP)

class Menu:
    def __init__(self, title, items):
        self.title = title
        self.items = items
        self.selected = 0

    def draw(self):
        oled.fill(0)
        # Dibujar el encabezado
        oled.fill_rect(0, 0, 128, 12, 1)
        oled.text(self.title, 2, 2, 0)
        
        # Listar los items del menú de CENTINEL
        for i, item in enumerate(self.items):
            y = 16 + (i * 10)
            if i == self.selected:
                oled.fill_rect(0, y-1, 128, 9, 1)
                oled.text(item, 10, y, 0)
                oled.text(">", 2, y, 0)
            else:
                oled.text(item, 10, y, 1)
        oled.show()

# Items para tu proyecto de auditoría táctica
phantom_menu = Menu("SENTINEL V1.0", ["WIFI SCAN", "DEAUTH", "BEACON", "SYS INFO", "REBOOT"])

print("Corriendo SENTINEL PHANTOM...")

while True:
    y_pos = vry.read_u16() # Valor entre 0 y 65535
    
    # Mover hacia arriba (el joystick suele dar valores bajos arriba)
    if y_pos < 10000:
        phantom_menu.selected = (phantom_menu.selected - 1) % len(phantom_menu.items)
        phantom_menu.draw()
        time.sleep(0.2) # Evita saltos múltiples
        
    # Mover hacia abajo (valores altos abajo)
    elif y_pos > 55000:
        phantom_menu.selected = (phantom_menu.selected + 1) % len(phantom_menu.items)
        phantom_menu.draw()
        time.sleep(0.2)

    # Si presionas el joystick (Click)
    if sw.value() == 0:
        oled.fill(0)
        oled.fill_rect(0, 25, 128, 15, 1)
        oled.text("STARTING...", 25, 30, 0)
        oled.show()
        time.sleep(1.0)
        phantom_menu.draw()

    phantom_menu.draw()
    time.sleep(0.1)