import time
import threading
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from joystick import JoystickADS1115 
# ── Dimensiones del SSD1306 ──────────────────────────────────────
W, H = 128, 64

# ── Estructura de menú ────────────────────────────────────────────
MENU = {
    "root": [
        {"label": "DEFENSA",       "submenu": "defense"},
        {"label": "ATAQUE",        "submenu": "attack"},
        {"label": "ESTADO",        "action":  "status"},
    ],
    "defense": [
        {"label": "IDS WiFi",      "action": "wifi_ids"},
        {"label": "BLE Scan",      "action": "ble_scan"},
        {"label": "TSCM Espectro", "action": "tscm_scan"},
        {"label": "Detect Drones", "action": "nrf24_scan"},
        {"label": "< Volver",      "back": True},
    ],
    "attack": [
        {"label": "Deauth WiFi",   "action": "wifi_deauth"},
        {"label": "Evil Twin",     "action": "wifi_evil_twin"},
        {"label": "BLE Disconnect","action": "ble_disconnect"},
        {"label": "MouseJack",     "action": "mousejack"},
        {"label": "< Volver",      "back": True},
    ],
}


class OledDisplay:
    def _init_(self, event_bus=None):
        # Inicializar hardware OLED
        serial = i2c(port=1, address=0x3C)
        self.device = ssd1306(serial, width=W, height=H)

        self.bus          = event_bus
        self.current_menu = "root"
        self.cursor       = 0
        self.scroll_off   = 0       # offset para listas largas
        self.MAX_VISIBLE  = 4       # ítems visibles en pantalla
        self.active_mod   = None    # módulo corriendo actualmente
        self.jostick = JoystickADS1115(self.bus, self)
        self._lock        = threading.Lock()

        # Fuente pequeña: usar la default de luma (no necesita PIL font)
        # Para el logo usarás tu imagen PNG — ver show_boot()

    # ══════════════════════════════════════════════════════════════
    # BOOT — logo + animación estilo Kali
    # ══════════════════════════════════════════════════════════════
    def show_boot(self, logo_path="assets/logo.png"):
        """
        Secuencia de arranque:
          1. Muestra tu logo centrado (imagen 128×40 px en blanco sobre negro)
          2. Barra de progreso animada
          3. Fade-out (pantalla parpadeante)

        Prepara tu logo: PNG monocromo 128×40 px, fondo negro, logo blanco.
        Puedes convertirlo con: convert logo.png -resize 128x40 -threshold 50% logo_bw.png
        """
        # — Fase 1: logo —
        try:
            logo = Image.open(logo_path).convert("1").resize((128, 40))
        except FileNotFoundError:
            logo = None

        with canvas(self.device) as draw:
            if logo:
                self.device.display(logo)
            else:
                # Fallback si no hay logo: texto grande
                draw.text((10, 5),  "SENTINEL",  fill="white")
                draw.text((10, 20), "PHANTOM",   fill="white")
                draw.text((10, 35), "v1.0",      fill="white")
        time.sleep(1.5)

        # — Fase 2: barra de progreso con texto de módulos —
        pasos = [
            (15,  "Iniciando core..."),
            (30,  "Cargando WiFi..."),
            (50,  "Cargando BLE..."),
            (65,  "Cargando RFID..."),
            (80,  "Cargando TSCM..."),
            (95,  "Cargando nRF24..."),
            (100, "Sistema listo."),
        ]
        for pct, texto in pasos:
            with canvas(self.device) as draw:
                # Logo pequeño arriba (o nombre)
                if logo:
                    logo_small = logo.resize((80, 20))
                    # pegar en canvas PIL
                    img = Image.new("1", (W, H), 0)
                    img.paste(logo_small, (24, 0))
                    d = ImageDraw.Draw(img)
                    # barra
                    d.rectangle([(0, 25), (126, 34)], outline=1)
                    d.rectangle([(1, 26), (int(124 * pct / 100), 33)], fill=1)
                    d.text((0, 37), texto,            fill=1)
                    d.text((100, 37), f"{pct}%",      fill=1)
                    self.device.display(img)
                else:
                    draw.text((0, 0),  "SENTINEL PHANTOM", fill="white")
                    draw.rectangle([(0, 15), (126, 24)], outline="white")
                    draw.rectangle([(1, 16), (int(124 * pct / 100), 23)], fill="white")
                    draw.text((0, 27), texto,         fill="white")
                    draw.text((100, 27), f"{pct}%",   fill="white")
            time.sleep(0.18)

        # — Fase 3: parpadeo de "listo" (estilo terminal) —
        for _ in range(4):
            self.device.hide()
            time.sleep(0.08)
            self.device.show()
            time.sleep(0.08)

        time.sleep(0.4)
        # Entrar al menú principal
        self.current_menu = "root"
        self.cursor       = 0
        self.draw_menu()

    # ══════════════════════════════════════════════════════════════
    # MENÚ — navegación jerárquica
    # ══════════════════════════════════════════════════════════════
    def draw_menu(self):
        """Renderiza el menú actual con cursor y scroll."""
        with self._lock:
            items = MENU[self.current_menu]
            # Calcular ventana de scroll
            if self.cursor < self.scroll_off:
                self.scroll_off = self.cursor
            if self.cursor >= self.scroll_off + self.MAX_VISIBLE:
                self.scroll_off = self.cursor - self.MAX_VISIBLE + 1

            with canvas(self.device) as draw:
                # Header
                header = "SENTINEL" if self.current_menu == "root" else self.current_menu.upper()
                draw.text((0, 0), header, fill="white")
                draw.line([(0, 9), (W - 1, 9)], fill="white")

                # Ítems visibles
                for i in range(self.MAX_VISIBLE):
                    idx = self.scroll_off + i
                    if idx >= len(items):
                        break
                    y    = 12 + i * 12
                    item = items[idx]
                    # Ícono de categoría
                    if "submenu" in item:
                        prefix = "[+] "
                    elif item.get("back"):
                        prefix = "<-- "
                    else:
                        prefix = " >  "

                    label = (prefix + item["label"])[:20]

                    if idx == self.cursor:
                        # Ítem seleccionado: fondo blanco, texto negro
                        draw.rectangle([(0, y), (W - 1, y + 10)], fill="white")
                        draw.text((2, y + 1), label, fill="black")
                    else:
                        draw.text((2, y + 1), label, fill="white")

                # Scrollbar derecho si hay más ítems
                if len(items) > self.MAX_VISIBLE:
                    bar_h = int((H - 12) * self.MAX_VISIBLE / len(items))
                    bar_y = 12 + int((H - 12) * self.scroll_off / len(items))
                    draw.rectangle([(W - 3, 12), (W - 1, H - 1)], outline="white")
                    draw.rectangle([(W - 3, bar_y), (W - 1, bar_y + bar_h)], fill="white")

                # Footer: número de ítem
                draw.text((0, H - 8), f"{self.cursor + 1}/{len(items)}", fill="white")

    # ══════════════════════════════════════════════════════════════
    # NAVEGACIÓN — joystick up/down y botón select
    # ══════════════════════════════════════════════════════════════
    def nav_up(self):
        items = MENU[self.current_menu]
        self.cursor = (self.cursor - 1) % len(items)
        self.draw_menu()

    def nav_down(self):
        items = MENU[self.current_menu]
        self.cursor = (self.cursor + 1) % len(items)
        self.draw_menu()

    def nav_select(self):
        items  = MENU[self.current_menu]
        item   = items[self.cursor]

        if item.get("back"):
            # Volver al menú raíz
            self.current_menu = "root"
            self.cursor       = 0
            self.scroll_off   = 0
            self.draw_menu()

        elif "submenu" in item:
            # Entrar al submenú
            self.current_menu = item["submenu"]
            self.cursor       = 0
            self.scroll_off   = 0
            self.draw_menu()

        elif "action" in item:
            # Ejecutar acción
            self._run_action(item["action"], item["label"])

    def nav_back(self):
        """Botón izquierda del joystick = volver."""
        if self.current_menu != "root":
            self.current_menu = "root"
            self.cursor       = 0
            self.scroll_off   = 0
            self.draw_menu()

    # ══════════════════════════════════════════════════════════════
    # ACCIONES — confirmación y ejecución
    # ══════════════════════════════════════════════════════════════
    def _run_action(self, action: str, label: str):
        """Muestra pantalla de confirmación antes de ejecutar."""
        self._show_confirm(label)

        def _exec():
            time.sleep(0.5)
            self.show_running(label)
            if self.bus:
                self.bus.publish("oled:action", {"action": action})

        threading.Thread(target=_exec, daemon=True).start()

    def _show_confirm(self, label: str):
        """Pantalla de confirmación tipo terminal."""
        with canvas(self.device) as draw:
            draw.rectangle([(2, 2), (W - 3, H - 3)], outline="white")
            draw.text((10, 6),  "EJECUTAR:",   fill="white")
            draw.text((6, 18),  label[:20],    fill="white")
            draw.line([(2, 30), (W - 3, 30)],  fill="white")
            draw.rectangle([(10, 36), (55, 48)], outline="white")
            draw.text((17, 38), "[ OK ]",      fill="white")
            draw.rectangle([(65, 36), (115, 48)], outline="white")
            draw.text((70, 38), "[ CANCEL ]",  fill="white")

    def show_running(self, label: str):
        """Pantalla de módulo activo con indicador pulsante."""
        def _pulse():
            dots = ["   ", ".  ", ".. ", "..."]
            i = 0
            while self.active_mod == label:
                with canvas(self.device) as draw:
                    draw.text((0, 0),  "[ ACTIVO ]",      fill="white")
                    draw.line([(0, 9), (W - 1, 9)],       fill="white")
                    draw.text((0, 12), label[:20],         fill="white")
                    draw.text((0, 26), f"Running{dots[i % 4]}", fill="white")
                    draw.text((0, 38), "Joystick: STOP",   fill="white")
                    draw.line([(0, 54), (W - 1, 54)],     fill="white")
                    draw.text((0, 56), "Click para detener", fill="white")
                time.sleep(0.4)
                i += 1

        self.active_mod = label
        threading.Thread(target=_pulse, daemon=True).start()

    def stop_running(self):
        """Detener módulo activo y volver al menú."""
        self.active_mod = None
        time.sleep(0.1)
        self.draw_menu()
        if self.bus:
            self.bus.publish("oled:stop", {})

    # ══════════════════════════════════════════════════════════════
    # PANTALLAS DE ESTADO Y ALERTA
    # ══════════════════════════════════════════════════════════════
    def show_alert(self, message: str, module: str, level: str = "critical"):
        """Alerta crítica con borde doble — interrumpe cualquier pantalla."""
        with canvas(self.device) as draw:
            draw.rectangle([(0, 0), (W - 1, H - 1)], outline="white")
            draw.rectangle([(2, 2), (W - 3, H - 3)], outline="white")
            tag = "!! ALERTA !!" if level == "critical" else "! AVISO !"
            draw.text((20, 5),  tag,             fill="white")
            draw.line([(2, 15), (W - 3, 15)],    fill="white")
            draw.text((2, 18),  message[:21],     fill="white")
            draw.text((2, 28),  message[21:42],   fill="white")
            draw.line([(2, 40), (W - 3, 40)],    fill="white")
            draw.text((2, 43),  f"MOD: {module}", fill="white")
            draw.text((2, 53),  "Click = ACK",   fill="white")

    def show_status(self, cpu=0, ram=0, temp=0, ip=""):
        """Pantalla de estado del sistema."""
        with canvas(self.device) as draw:
            draw.text((22, 0),  "[ ESTADO ]",     fill="white")
            draw.line([(0, 9), (W - 1, 9)],       fill="white")
            draw.text((0, 12), f"CPU: {cpu}%  {temp:.1f}C", fill="white")
            draw.text((0, 22), f"RAM: {ram}%",    fill="white")
            draw.text((0, 32), f"IP: {ip}",       fill="white")
            draw.line([(0, 43), (W - 1, 43)],     fill="white")
            draw.text((0, 46), "WiFi BLE RFID nRF", fill="white")
            draw.text((0, 56), "Click = Volver",  fill="white")

    def cleanup(self):
        self.device.cleanup()
