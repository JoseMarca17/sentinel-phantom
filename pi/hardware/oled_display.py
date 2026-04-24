import time
from PIL import Image, ImageDraw
import adafruit_ssd1306
from hardware.splash import run_splash

W, H = 128, 64

MENU = {
    "root": [
        {"label": "DEFENSA",  "submenu": "defense"},
        {"label": "ATAQUE",   "submenu": "attack"},
        {"label": "ESTADO",   "action":  "status"},
    ],
    "defense": [
        {"label": "WiFi IDS",   "submenu": "wifi_defense"},
        {"label": "BT Scanner", "submenu": "bt_defense"},
        {"label": "< Volver",   "back": True},
    ],
    "attack": [
        {"label": "WiFi",      "submenu": "wifi_attack"},
        {"label": "RFID",      "submenu": "cloner_rfid"},
        {"label": "Inhibidor", "submenu": "inhibidor"},
        {"label": "< Volver",  "back": True},
    ],
    "wifi_defense": [
        {"label": "Iniciar IDS",   "action":  "wifi_ids_start"},
        {"label": "Detener IDS",   "action":  "wifi_ids_stop"},
        {"label": "Detector WiFi", "action":  "wifi_detector"},
        {"label": "Sniffer",       "submenu": "wifi_sniffer"},
        {"label": "< Volver",      "back": True},
    ],
    "wifi_sniffer": [
        {"label": "Iniciar",  "action": "wifi_sniffer_start"},
        {"label": "Detener",  "action": "wifi_sniffer_stop"},
        {"label": "Ver devs", "action": "wifi_sniffer_devices"},
        {"label": "< Volver", "back": True},
    ],
    "wifi_attack": [
        {"label": "Deauth",       "action": "wifi_deauth"},
        {"label": "Beacon Flood", "action": "wifi_beacon_flood"},
        {"label": "Evil Twin",    "action": "wifi_evil_twin"},
        {"label": "< Volver",     "back": True},
    ],
    "bt_defense": [
        {"label": "Scan BLE", "action": "bt_scan"},
        {"label": "< Volver", "back": True},
    ],
    "inhibidor": [
        {"label": "WiFi Jam", "action": "nrf_wifi_scan"},
        {"label": "BT Jam",   "action": "nrf_bt"},
        {"label": "< Volver", "back": True},
    ],
    "cloner_rfid": [
        {"label": "CLONAR RFID", "action": "clone_rfid"},
        {"label": "< Volver",    "back": True},
    ],
}

ACTION_LABELS = {
    "wifi_ids_start":       "WiFi",
    "wifi_ids_stop":        "WiFi",
    "wifi_detector":        "WiFi",
    "wifi_deauth":          "WiFi",
    "wifi_beacon_flood":    "WiFi",
    "wifi_evil_twin":       "WiFi",
    "wifi_sniffer_start":   "WiFi",
    "wifi_sniffer_stop":    "WiFi",
    "wifi_sniffer_devices": "WiFi",
    "bt_scan":              "BT",
    "clone_rfid":           "RFID",
    "status":               "ESTADO",
    "nrf_wifi_scan":        "INHIBIDOR",
    "nrf_bt":               "INHIBIDOR",
}

# AGREGAR esta constante junto a ACTION_LABELS:
SILENT_ACTIONS = {
    "wifi_sniffer_start",
    "wifi_sniffer_stop",
    "wifi_ids_stop",
}

_VISIBLE_ROWS = 4


class OledDisplay:

    def __init__(self, event_bus, i2c_lock, i2c_bus):
        self.bus  = event_bus
        self.lock = i2c_lock

        self.device = adafruit_ssd1306.SSD1306_I2C(W, H, i2c_bus)
        self.image  = Image.new("1", (W, H))
        self.draw   = ImageDraw.Draw(self.image)

        self.current_menu = "root"
        self.cursor = 0
        self.stack  = []
        self.mode   = "menu"   # menu | busy | wifi_select | bt_active | sniffer_devices

        self._wifi_nets   = []
        self._wifi_offset = 0

        self._wifi_cancel_menu    = "inhibidor"
        self._wifi_confirm_action = "nrf_wifi_attack"

        # Sniffer
        self._sniffer_devs   = []
        self._sniffer_offset = 0

        if self.bus:
            self.bus.subscribe("nav:up",           lambda _: self.nav_up())
            self.bus.subscribe("nav:down",         lambda _: self.nav_down())
            self.bus.subscribe("nav:left",         lambda _: self.nav_back())
            self.bus.subscribe("nav:select",       lambda _: self.nav_select())

            self.bus.subscribe("oled:rfid_status",     self.show_rfid_status)
            self.bus.subscribe("oled:wifi_status",     self.show_wifi_status)
            self.bus.subscribe("oled:bt_status",       self.show_bt_status)
            self.bus.subscribe("oled:bt_device",       self.show_bt_device)
            self.bus.subscribe("oled:status",          self.show_status)
            self.bus.subscribe("oled:return_menu",     lambda _: self.return_to_menu())
            self.bus.subscribe("oled:wifi_nets",       self.show_wifi_select)
            self.bus.subscribe("oled:bt_active",       self._show_bt_active)
            self.bus.subscribe("oled:sniffer_devices", self.show_sniffer_devices)
                        # AGREGAR junto a las otras suscripciones:
            self.bus.subscribe("oled:sniffer_progress", self.show_sniffer_progress)

    # ── RENDER ────────────────────────────────────────────────────────────────

    def _render(self):
        self.device.image(self.image)
        self.device.show()

    def clear(self):
        self.draw.rectangle((0, 0, W, H), fill=0)

    def show_boot(self):
        run_splash(self)

    # ── MENÚ ──────────────────────────────────────────────────────────────────

    def draw_menu(self):
        self.mode = "menu"
        with self.lock:
            self.clear()
            items = MENU[self.current_menu]
            self.draw.text((0, 0), self.current_menu.upper(), fill=255)
            for i, item in enumerate(items):
                prefix = ">" if i == self.cursor else " "
                self.draw.text((0, 15 + i * 12), f"{prefix} {item['label']}", fill=255)
            self._render()

    # ── WIFI SELECT ───────────────────────────────────────────────────────────

    def show_wifi_select(self, event):
        nets = event["payload"].get("networks", [])

        if not nets:
            self.show_wifi_status({"payload": {"msg": "Sin redes"}})
            time.sleep(1.5)
            self.return_to_menu()
            return

        sample_action = nets[0].get("attack_action", "")
        if sample_action:
            self._wifi_confirm_action = sample_action
            self._wifi_cancel_menu    = "wifi_attack"
        else:
            self._wifi_confirm_action = "nrf_wifi_attack"
            self._wifi_cancel_menu    = "inhibidor"

        self._wifi_nets   = list(nets) + [{"ssid": "< Volver", "ch": None, "rssi": None, "_back": True}]
        self._wifi_offset = 0
        self.cursor       = 0
        self.mode         = "wifi_select"
        self._draw_wifi_select()

    def _draw_wifi_select(self):
        with self.lock:
            self.clear()
            self.draw.text((0, 0), "SEL RED >OK", fill=255)

            visible = self._wifi_nets[self._wifi_offset:self._wifi_offset + _VISIBLE_ROWS]
            for i, net in enumerate(visible):
                abs_idx = self._wifi_offset + i
                prefix  = ">" if abs_idx == self.cursor else " "

                if net.get("_back"):
                    label = f"{prefix} < Volver"
                else:
                    label = f"{prefix}{net['ssid'][:10]} {net['ch']} {net['rssi']}"

                self.draw.text((0, 15 + i * 12), label[:21], fill=255)

            self._render()

    # ── SNIFFER DEVICES ───────────────────────────────────────────────────────

    def show_sniffer_devices(self, event):
        devices = event["payload"].get("devices", [])

        if not devices:
            self.show_wifi_status({"payload": {"msg": "Sin dispositivos"}})
            time.sleep(1.5)
            self.return_to_menu()
            return

        self._sniffer_devs   = list(devices) + [{"_back": True}]
        self._sniffer_offset = 0
        self.cursor          = 0
        self.mode            = "sniffer_devices"
        self._draw_sniffer_devices()

    def show_sniffer_progress(self, event):
        devices = event["payload"].get("devices", [])
        elapsed = event["payload"].get("elapsed", 0)
        total   = event["payload"].get("total",   20)
        remaining = total - elapsed

        with self.lock:
            self.clear()
            self.draw.text((0, 0),  "SNIFFING...", fill=255)
            self.draw.text((0, 14), f"Devs: {len(devices)}", fill=255)

            # Barra de progreso
            bar_w = int((elapsed / total) * 100) if total > 0 else 0
            self.draw.rectangle((0, 28, 100, 36), outline=255, fill=0)
            if bar_w > 0:
                self.draw.rectangle((0, 28, bar_w, 36), fill=255)

            self.draw.text((0, 40), f"Resto: {remaining}s", fill=255)

            # Mostrar últimos dispositivos encontrados
            if devices:
                last = devices[-1]
                ip   = last.get("ip", "??")
                self.draw.text((0, 52), f"{ip[:20]}", fill=255)

            self._render()
        
    def _draw_sniffer_devices(self):
        with self.lock:
            self.clear()
            self.draw.text((0, 0), "DISPOSITIVOS", fill=255)

            visible = self._sniffer_devs[
                self._sniffer_offset:self._sniffer_offset + _VISIBLE_ROWS
            ]
            for i, dev in enumerate(visible):
                abs_idx = self._sniffer_offset + i
                prefix  = ">" if abs_idx == self.cursor else " "

                if dev.get("_back"):
                    label = f"{prefix} < Volver"
                else:
                    ip  = dev.get("ip",  "??")
                    mac = dev.get("mac", "??")[-8:]
                    label = f"{prefix}{ip[:13]} {mac}"

                self.draw.text((0, 15 + i * 12), label[:21], fill=255)

            self._render()

    # ── BT ACTIVO ─────────────────────────────────────────────────────────────

    def _show_bt_active(self, event=None):
        self.mode = "bt_active"
        with self.lock:
            self.clear()
            self.draw.text((0, 0),  "BT JAM ACTIVO", fill=255)
            self.draw.text((0, 20), "~~~~~~~~~~~~~~", fill=255)
            self.draw.text((0, 36), "> DETENER",      fill=255)
            self.draw.text((0, 52), "  OK o < detiene", fill=255)
            self._render()

    # ── NAVEGACIÓN ────────────────────────────────────────────────────────────

    def nav_up(self):
        if self.mode == "sniffer_devices":
            if self.cursor > 0:
                self.cursor -= 1
                if self.cursor < self._sniffer_offset:
                    self._sniffer_offset = self.cursor
            self._draw_sniffer_devices()
            return

        if self.mode == "wifi_select":
            if self.cursor > 0:
                self.cursor -= 1
                if self.cursor < self._wifi_offset:
                    self._wifi_offset = self.cursor
            self._draw_wifi_select()
            return

        if self.mode == "menu":
            self.cursor = (self.cursor - 1) % len(MENU[self.current_menu])
            self.draw_menu()

    def nav_down(self):
        if self.mode == "sniffer_devices":
            if self.cursor < len(self._sniffer_devs) - 1:
                self.cursor += 1
                if self.cursor >= self._sniffer_offset + _VISIBLE_ROWS:
                    self._sniffer_offset = self.cursor - _VISIBLE_ROWS + 1
            self._draw_sniffer_devices()
            return

        if self.mode == "wifi_select":
            if self.cursor < len(self._wifi_nets) - 1:
                self.cursor += 1
                if self.cursor >= self._wifi_offset + _VISIBLE_ROWS:
                    self._wifi_offset = self.cursor - _VISIBLE_ROWS + 1
            self._draw_wifi_select()
            return

        if self.mode == "menu":
            self.cursor = (self.cursor + 1) % len(MENU[self.current_menu])
            self.draw_menu()

    def nav_select(self):
        if self.mode == "bt_active":
            self.bus.publish_sync("oled:action", {"action": "nrf_stop"})
            return

        if self.mode == "sniffer_devices":
            dev = self._sniffer_devs[self.cursor]
            if dev.get("_back"):
                self.mode = "menu"
                self.current_menu = "wifi_sniffer"
                self.cursor = 0
                self.draw_menu()
            return

        if self.mode == "wifi_select":
            net = self._wifi_nets[self.cursor]
            if net.get("_back"):
                self._cancel_wifi_select()
                return
            self.bus.publish_sync("oled:action", {
                "action":  self._wifi_confirm_action,
                "net_idx": self.cursor,
            })
            return

        if self.mode != "menu":
            return

        item = MENU[self.current_menu][self.cursor]

        if item.get("back"):
            self.nav_back()
            return

        if "submenu" in item:
            self.stack.append(self.current_menu)
            self.current_menu = item["submenu"]
            self.cursor = 0
            self.draw_menu()
            return

        if "action" in item:
            self.run_action(item["action"], item["label"])

    def nav_back(self):
        if self.mode == "bt_active":
            self.bus.publish_sync("oled:action", {"action": "nrf_stop"})
            return

        if self.mode == "sniffer_devices":
            self.mode = "menu"
            self.current_menu = "wifi_sniffer"
            self.cursor = 0
            self.draw_menu()
            return

        if self.mode == "wifi_select":
            self._cancel_wifi_select()
            return

        if self.mode != "menu":
            return

        if self.stack:
            self.current_menu = self.stack.pop()
            self.cursor = 0
            self.draw_menu()

    def _cancel_wifi_select(self):
        self.mode = "menu"
        self.current_menu = self._wifi_cancel_menu
        self.cursor = 0
        self.draw_menu()

    # ── ACCIÓN ────────────────────────────────────────────────────────────────

    def run_action(self, action, label):
        # Acciones que no necesitan pantalla de busy
        if action in SILENT_ACTIONS:
            if self.bus:
                self.bus.publish_sync("oled:action", {"action": action})
            return

        self.mode = "busy"
        module_title = ACTION_LABELS.get(action, label)

        with self.lock:
            self.clear()
            self.draw.text((0, 0),  module_title, fill=255)
            self.draw.text((0, 25), label[:20],   fill=255)
            self._render()

        if self.bus:
            self.bus.publish_sync("oled:action", {"action": action})

    # ── STATUS HANDLERS ───────────────────────────────────────────────────────

    def show_rfid_status(self, event):
        msg = event["payload"]["msg"]
        with self.lock:
            self.clear()
            self.draw.text((0, 0),  "RFID",   fill=255)
            self.draw.text((0, 25), msg[:20], fill=255)
            self._render()

    def show_wifi_status(self, event):
        msg = event["payload"]["msg"]
        with self.lock:
            self.clear()
            self.draw.text((0, 0),  "WiFi",   fill=255)
            self.draw.text((0, 25), msg[:20], fill=255)
            self._render()

    def show_bt_status(self, event):
        msg = event["payload"]["msg"]
        with self.lock:
            self.clear()
            self.draw.text((0, 0),  "BT",     fill=255)
            self.draw.text((0, 25), msg[:20], fill=255)
            self._render()

    def show_bt_device(self, event):
        p = event["payload"]
        with self.lock:
            self.clear()
            self.draw.text((0, 0),  f"BT {p['index']}/{p['total']}", fill=255)
            self.draw.text((0, 16), p['name'][:20],   fill=255)
            self.draw.text((0, 30), p['vendor'][:20], fill=255)
            self.draw.text((0, 44), p['mac'],          fill=255)
            self._render()

    def show_status(self, event):
        lines = event["payload"]["lines"]
        with self.lock:
            self.clear()
            self.draw.text((0, 0), "ESTADO", fill=255)
            for i, line in enumerate(lines):
                self.draw.text((0, 18 + i * 12), line[:20], fill=255)
            self._render()

    # ── RETORNO AL MENÚ ───────────────────────────────────────────────────────

    def return_to_menu(self):
        if self.stack:
            self.current_menu = self.stack.pop()
        else:
            self.current_menu = "root"
        self.cursor = 0
        self.draw_menu()

    def cleanup(self):
        self.device.fill(0)
        self.device.show()