# import time
# import threading
# from PIL import Image, ImageDraw, ImageFont
# from luma.core.interface.serial import i2c
# from luma.oled.device import ssd1306
# from luma.core.render import canvas

# # ── Dimensiones del SSD1306 ──────────────────────────────────────
# W, H = 128, 64

# # ── Estructura de menú ────────────────────────────────────────────
# MENU = {
#     "root": [
#         {"label": "DEFENSA",       "submenu": "defense"},
#         {"label": "ATAQUE",        "submenu": "attack"},
#         {"label": "ESTADO",        "action":  "status"},
#     ],
#     "defense": [
#         {"label": "IDS WiFi",      "action": "wifi_ids"},
#         {"label": "BLE Scan",      "action": "ble_scan"},
#         {"label": "TSCM Espectro", "action": "tscm_scan"},
#         {"label": "Detect Drones", "action": "nrf24_scan"},
#         {"label": "< Volver",      "back": True},
#     ],
#     "attack": [
#         {"label": "Deauth WiFi",   "action": "wifi_deauth"},
#         {"label": "Evil Twin",     "action": "wifi_evil_twin"},
#         {"label": "BLE Disconnect","action": "ble_disconnect"},
#         {"label": "MouseJack",     "action": "mousejack"},
#         {"label": "< Volver",      "back": True},
#     ],
# }

# class OledDisplay:
#     def __init__(self, event_bus=None, i2c_lock=None):
#         self.bus = event_bus
#         self.lock = i2c_lock or threading.Lock()
#         print('OLED LOCK:',id(self.lock))
#         serial = i2c(port=1, address=0x3C)
#         self.device = ssd1306(serial, width=W, height=H)

#         self.current_menu = "root"
#         self.cursor = 0
#         self.scroll_off = 0       # offset para listas largas
#         self.MAX_VISIBLE = 4      # ítems visibles en pantalla
#         self.active_mod = None    # módulo corriendo actualmente

#         if self.bus:
#             self.bus.subscribe("nav:up", lambda _: self.nav_up())
#             self.bus.subscribe("nav:down", lambda _: self.nav_down())
#             self.bus.subscribe("nav:left", lambda _: self.nav_back())
#             self.bus.subscribe("nav:select", lambda _: self._handle_select())

#     def _handle_select(self):
#         if self.active_mod:
#             self.stop_running()
#         else:
#             self.nav_select()

#     def show_boot(self, logo_path="assets/logo.png"):
#         # — Fase 1: logo —
#         try:
#             logo = Image.open(logo_path).convert("1").resize((128, 40))
#         except FileNotFoundError:
#             logo = None

#         with self.lock:
#             with canvas(self.device) as draw:
#                 if logo:
#                     self.device.display(logo)
#                 else:
#                     draw.text((10, 5),  "SENTINEL",  fill="white")
#                     draw.text((10, 20), "PHANTOM",   fill="white")
#                     draw.text((10, 35), "v1.0",      fill="white")
#             time.sleep(1.5)

#         # — Fase 2: barra de progreso —
#         pasos = [
#             (15,  "Iniciando core..."),
#             (30,  "Cargando WiFi..."),
#             (50,  "Cargando BLE..."),
#             (65,  "Cargando RFID..."),
#             (80,  "Cargando TSCM..."),
#             (95,  "Cargando nRF24..."),
#             (100, "Sistema listo."),
#         ]

#         for pct, texto in pasos:
#             with self.lock:
#                 with canvas(self.device) as draw:
#                     if logo:
#                         logo_small = logo.resize((80, 20))
#                         img = Image.new("1", (W, H), 0)
#                         img.paste(logo_small, (24, 0))
#                         d = ImageDraw.Draw(img)
#                         d.rectangle([(0, 25), (126, 34)], outline=1)
#                         d.rectangle([(1, 26), (int(124 * pct / 100), 33)], fill=1)
#                         d.text((0, 37), texto, fill=1)
#                         d.text((100, 37), f"{pct}%", fill=1)
#                         self.device.display(img)
#                     else:
#                         draw.text((0, 0), "SENTINEL PHANTOM", fill="white")
#                         draw.rectangle([(0, 15), (126, 24)], outline="white")
#                         draw.rectangle([(1, 16), (int(124 * pct / 100), 23)], fill="white")
#                         draw.text((0, 27), texto, fill="white")
#                         draw.text((100, 27), f"{pct}%", fill="white")
#             time.sleep(0.18)

#         # — Fase 3: parpadeo —
#         for _ in range(4):
#             self.device.hide()
#             time.sleep(0.08)
#             self.device.show()
#             time.sleep(0.08)

#         time.sleep(0.4)
#         self.current_menu = "root"
#         self.cursor = 0
#         self.draw_menu()

#     def draw_menu(self):
#         with self.lock:
#             items = MENU[self.current_menu]
#             if self.cursor < self.scroll_off:
#                 self.scroll_off = self.cursor
#             if self.cursor >= self.scroll_off + self.MAX_VISIBLE:
#                 self.scroll_off = self.cursor - self.MAX_VISIBLE + 1

#             with canvas(self.device) as draw:
#                 header = "SENTINEL" if self.current_menu == "root" else self.current_menu.upper()
#                 draw.text((0, 0), header, fill="white")
#                 draw.line([(0, 9), (W - 1, 9)], fill="white")

#                 for i in range(self.MAX_VISIBLE):
#                     idx = self.scroll_off + i
#                     if idx >= len(items):
#                         break
#                     y = 12 + i * 12
#                     item = items[idx]
                    
#                     if "submenu" in item:
#                         prefix = "[+] "
#                     elif item.get("back"):
#                         prefix = "<-- "
#                     else:
#                         prefix = " >  "

#                     label = (prefix + item["label"])[:20]

#                     if idx == self.cursor:
#                         draw.rectangle([(0, y), (W - 1, y + 10)], fill="white")
#                         draw.text((2, y + 1), label, fill="black")
#                     else:
#                         draw.text((2, y + 1), label, fill="white")

#                 if len(items) > self.MAX_VISIBLE:
#                     bar_h = int((H - 12) * self.MAX_VISIBLE / len(items))
#                     bar_y = 12 + int((H - 12) * self.scroll_off / len(items))
#                     draw.rectangle([(W - 3, 12), (W - 1, H - 1)], outline="white")
#                     draw.rectangle([(W - 3, bar_y), (W - 1, bar_y + bar_h)], fill="white")

#                 draw.text((0, H - 8), f"{self.cursor + 1}/{len(items)}", fill="white")

#     def nav_up(self):
#         items = MENU[self.current_menu]
#         self.cursor = (self.cursor - 1) % len(items)
#         self.draw_menu()

#     def nav_down(self):
#         items = MENU[self.current_menu]
#         self.cursor = (self.cursor + 1) % len(items)
#         self.draw_menu()

#     def nav_select(self):
#         items = MENU[self.current_menu]
#         item = items[self.cursor]

#         if item.get("back"):
#             self.current_menu = "root"
#             self.cursor = 0
#             self.scroll_off = 0
#             self.draw_menu()
#         elif "submenu" in item:
#             self.current_menu = item["submenu"]
#             self.cursor = 0
#             self.scroll_off = 0
#             self.draw_menu()
#         elif "action" in item:
#             self._run_action(item["action"], item["label"])

#     def nav_back(self):
#         if self.current_menu != "root":
#             self.current_menu = "root"
#             self.cursor = 0
#             self.scroll_off = 0
#             self.draw_menu()

#     def _run_action(self, action: str, label: str):
#         self._show_confirm(label)
#         def _exec():
#             time.sleep(0.5)
#             self.show_running(label)
#             if self.bus:
#                 self.bus.publish("oled:action", {"action": action})
#         threading.Thread(target=_exec, daemon=True).start()

#     def _show_confirm(self, label: str):
#         with self.lock:
#             with canvas(self.device) as draw:
#                 draw.rectangle([(2, 2), (W - 3, H - 3)], outline="white")
#                 draw.text((10, 6),  "EJECUTAR:",   fill="white")
#                 draw.text((6, 18),  label[:20],    fill="white")
#                 draw.line([(2, 30), (W - 3, 30)],  fill="white")
#                 draw.rectangle([(10, 36), (55, 48)], outline="white")
#                 draw.text((17, 38), "[ OK ]",      fill="white")
#                 draw.rectangle([(65, 36), (115, 48)], outline="white")
#                 draw.text((70, 38), "[ CANCEL ]",  fill="white")

#     def show_running(self, label: str):
#         self.active_mod = label
#         def _pulse():
#             dots = ["   ", ".  ", ".. ", "..."]
#             i = 0
#             while self.active_mod == label:
#                 with self.lock:
#                     with canvas(self.device) as draw:
#                         draw.text((0, 0),  "[ ACTIVO ]",      fill="white")
#                         draw.line([(0, 9), (W - 1, 9)],       fill="white")
#                         draw.text((0, 12), label[:20],         fill="white")
#                         draw.text((0, 26), f"Running{dots[i % 4]}", fill="white")
#                         draw.text((0, 38), "Joystick: STOP",   fill="white")
#                         draw.line([(0, 54), (W - 1, 54)],     fill="white")
#                         draw.text((0, 56), "Click para detener", fill="white")
#                 time.sleep(0.4)
#                 i += 1
#         threading.Thread(target=_pulse, daemon=True).start()

#     def stop_running(self):
#         self.active_mod = None
#         time.sleep(0.1)
#         self.draw_menu()
#         if self.bus:
#             self.bus.publish("oled:stop", {})

#     def show_alert(self, message: str, module: str, level: str = "critical"):
#         with self.lock:
#             with canvas(self.device) as draw:
#                 draw.rectangle([(0, 0), (W - 1, H - 1)], outline="white")
#                 draw.rectangle([(2, 2), (W - 3, H - 3)], outline="white")
#                 tag = "!! ALERTA !!" if level == "critical" else "! AVISO !"
#                 draw.text((20, 5),  tag,             fill="white")
#                 draw.line([(2, 15), (W - 3, 15)],    fill="white")
#                 draw.text((2, 18),  message[:21],     fill="white")
#                 draw.text((2, 28),  message[21:42],   fill="white")
#                 draw.line([(2, 40), (W - 3, 40)],    fill="white")
#                 draw.text((2, 43),  f"MOD: {module}", fill="white")
#                 draw.text((2, 53),  "Click = ACK",   fill="white")

#     def show_status(self, cpu=0, ram=0, temp=0, ip=""):
#         with self.lock:
#             with canvas(self.device) as draw:
#                 draw.text((22, 0),  "[ ESTADO ]",     fill="white")
#                 draw.line([(0, 9), (W - 1, 9)],       fill="white")
#                 draw.text((0, 12), f"CPU: {cpu}%  {temp:.1f}C", fill="white")
#                 draw.text((0, 22), f"RAM: {ram}%",    fill="white")
#                 draw.text((0, 32), f"IP: {ip}",       fill="white")
#                 draw.line([(0, 43), (W - 1, 43)],     fill="white")
#                 draw.text((0, 46), "WiFi BLE RFID nRF", fill="white")
#                 draw.text((0, 56), "Click = Volver",  fill="white")

#     def cleanup(self):
#         self.device.cleanup()


# import time
# import threading
# from PIL import Image, ImageDraw, ImageFont
# from luma.core.interface.serial import i2c
# from luma.oled.device import ssd1306
# from luma.core.render import canvas

# # ── Dimensiones del SSD1306 ──────────────────────────────────────
# W, H = 128, 64

# # ── Estructura de menú ────────────────────────────────────────────
# MENU = {
#     "root": [
#         {"label": "DEFENSA",       "submenu": "defense"},
#         {"label": "ATAQUE",        "submenu": "attack"},
#         {"label": "ESTADO",        "action":  "status"},
#     ],
#     "defense": [
#         {"label": "IDS WiFi",      "action": "wifi_ids"},
#         {"label": "BLE Scan",      "action": "ble_scan"},
#         {"label": "TSCM Espectro", "action": "tscm_scan"},
#         {"label": "Detect Drones", "action": "nrf24_scan"},
#         {"label": "< Volver",      "back": True},
#     ],
#     "attack": [
#         {"label": "Deauth WiFi",   "action": "wifi_deauth"},
#         {"label": "Evil Twin",     "action": "wifi_evil_twin"},
#         {"label": "BLE Disconnect","action": "ble_disconnect"},
#         {"label": "MouseJack",     "action": "mousejack"},
#         {"label": "< Volver",      "back": True},
#     ],
# }

# class OledDisplay:
#     def __init__(self, event_bus=None, i2c_lock=None):
#         self.bus = event_bus
#         self.lock = i2c_lock or threading.Lock()
#         print('OLED LOCK:', id(self.lock))
#         serial = i2c(port=1, address=0x3C)
#         self.device = ssd1306(serial, width=W, height=H)

#         self.current_menu = "root"
#         self.cursor = 0
#         self.scroll_off = 0       # offset para listas largas
#         self.MAX_VISIBLE = 4      # ítems visibles en pantalla
#         self.active_mod = None    # módulo corriendo actualmente

#         if self.bus:
#             self.bus.subscribe("nav:up", lambda _: self.nav_up())
#             self.bus.subscribe("nav:down", lambda _: self.nav_down())
#             self.bus.subscribe("nav:left", lambda _: self.nav_back())
#             self.bus.subscribe("nav:select", lambda _: self._handle_select())

#     def _handle_select(self):
#         if self.active_mod:
#             self.stop_running()
#         else:
#             self.nav_select()

#     def show_boot(self, logo_path="assets/logo.png"):
#         # — Fase 1: logo —
#         try:
#             logo = Image.open(logo_path).convert("1").resize((128, 40))
#         except FileNotFoundError:
#             logo = None

#         with self.lock:
#             with canvas(self.device) as draw:
#                 if logo:
#                     self.device.display(logo)
#                 else:
#                     draw.text((10, 5),  "SENTINEL",  fill="white")
#                     draw.text((10, 20), "PHANTOM",   fill="white")
#                     draw.text((10, 35), "v1.0",      fill="white")
#             time.sleep(1.5)

#         # — Fase 2: barra de progreso —
#         pasos = [
#             (15,  "Iniciando core..."),
#             (30,  "Cargando WiFi..."),
#             (50,  "Cargando BLE..."),
#             (65,  "Cargando RFID..."),
#             (80,  "Cargando TSCM..."),
#             (95,  "Cargando nRF24..."),
#             (100, "Sistema listo."),
#         ]

#         for pct, texto in pasos:
#             with self.lock:
#                 with canvas(self.device) as draw:
#                     if logo:
#                         logo_small = logo.resize((80, 20))
#                         img = Image.new("1", (W, H), 0)
#                         img.paste(logo_small, (24, 0))
#                         d = ImageDraw.Draw(img)
#                         d.rectangle([(0, 25), (126, 34)], outline=1)
#                         d.rectangle([(1, 26), (int(124 * pct / 100), 33)], fill=1)
#                         d.text((0, 37), texto, fill=1)
#                         d.text((100, 37), f"{pct}%", fill=1)
#                         self.device.display(img)
#                     else:
#                         draw.text((0, 0), "SENTINEL PHANTOM", fill="white")
#                         draw.rectangle([(0, 15), (126, 24)], outline="white")
#                         draw.rectangle([(1, 16), (int(124 * pct / 100), 23)], fill="white")
#                         draw.text((0, 27), texto, fill="white")
#                         draw.text((100, 27), f"{pct}%", fill="white")
#             time.sleep(0.18)

#         # — Fase 3: parpadeo — (lock en cada operación de dispositivo)
#         for _ in range(4):
#             with self.lock:
#                 self.device.hide()
#             time.sleep(0.08)
#             with self.lock:
#                 self.device.show()
#             time.sleep(0.08)

#         time.sleep(0.4)
#         self.current_menu = "root"
#         self.cursor = 0
#         self.draw_menu()

#     def draw_menu(self):
#         with self.lock:
#             items = MENU[self.current_menu]
#             if self.cursor < self.scroll_off:
#                 self.scroll_off = self.cursor
#             if self.cursor >= self.scroll_off + self.MAX_VISIBLE:
#                 self.scroll_off = self.cursor - self.MAX_VISIBLE + 1

#             with canvas(self.device) as draw:
#                 header = "SENTINEL" if self.current_menu == "root" else self.current_menu.upper()
#                 draw.text((0, 0), header, fill="white")
#                 draw.line([(0, 9), (W - 1, 9)], fill="white")

#                 for i in range(self.MAX_VISIBLE):
#                     idx = self.scroll_off + i
#                     if idx >= len(items):
#                         break
#                     y = 12 + i * 12
#                     item = items[idx]

#                     if "submenu" in item:
#                         prefix = "[+] "
#                     elif item.get("back"):
#                         prefix = "<-- "
#                     else:
#                         prefix = " >  "

#                     label = (prefix + item["label"])[:20]

#                     if idx == self.cursor:
#                         draw.rectangle([(0, y), (W - 1, y + 10)], fill="white")
#                         draw.text((2, y + 1), label, fill="black")
#                     else:
#                         draw.text((2, y + 1), label, fill="white")

#                 if len(items) > self.MAX_VISIBLE:
#                     bar_h = int((H - 12) * self.MAX_VISIBLE / len(items))
#                     bar_y = 12 + int((H - 12) * self.scroll_off / len(items))
#                     draw.rectangle([(W - 3, 12), (W - 1, H - 1)], outline="white")
#                     draw.rectangle([(W - 3, bar_y), (W - 1, bar_y + bar_h)], fill="white")

#                 draw.text((0, H - 8), f"{self.cursor + 1}/{len(items)}", fill="white")

#     def nav_up(self):
#         items = MENU[self.current_menu]
#         self.cursor = (self.cursor - 1) % len(items)
#         self.draw_menu()

#     def nav_down(self):
#         items = MENU[self.current_menu]
#         self.cursor = (self.cursor + 1) % len(items)
#         self.draw_menu()

#     def nav_select(self):
#         items = MENU[self.current_menu]
#         item = items[self.cursor]

#         if item.get("back"):
#             self.current_menu = "root"
#             self.cursor = 0
#             self.scroll_off = 0
#             self.draw_menu()
#         elif "submenu" in item:
#             self.current_menu = item["submenu"]
#             self.cursor = 0
#             self.scroll_off = 0
#             self.draw_menu()
#         elif "action" in item:
#             self._run_action(item["action"], item["label"])

#     def nav_back(self):
#         if self.current_menu != "root":
#             self.current_menu = "root"
#             self.cursor = 0
#             self.scroll_off = 0
#             self.draw_menu()

#     def _run_action(self, action: str, label: str):
#         self._show_confirm(label)
#         def _exec():
#             time.sleep(0.5)
#             self.show_running(label)
#             if self.bus:
#                 self.bus.publish("oled:action", {"action": action})
#         threading.Thread(target=_exec, daemon=True).start()

#     def _show_confirm(self, label: str):
#         with self.lock:
#             with canvas(self.device) as draw:
#                 draw.rectangle([(2, 2), (W - 3, H - 3)], outline="white")
#                 draw.text((10, 6),  "EJECUTAR:",   fill="white")
#                 draw.text((6, 18),  label[:20],    fill="white")
#                 draw.line([(2, 30), (W - 3, 30)],  fill="white")
#                 draw.rectangle([(10, 36), (55, 48)], outline="white")
#                 draw.text((17, 38), "[ OK ]",      fill="white")
#                 draw.rectangle([(65, 36), (115, 48)], outline="white")
#                 draw.text((70, 38), "[ CANCEL ]",  fill="white")

#     def show_running(self, label: str):
#         self.active_mod = label
#         def _pulse():
#             dots = ["   ", ".  ", ".. ", "..."]
#             i = 0
#             while self.active_mod == label:
#                 with self.lock:
#                     with canvas(self.device) as draw:
#                         draw.text((0, 0),  "[ ACTIVO ]",      fill="white")
#                         draw.line([(0, 9), (W - 1, 9)],       fill="white")
#                         draw.text((0, 12), label[:20],         fill="white")
#                         draw.text((0, 26), f"Running{dots[i % 4]}", fill="white")
#                         draw.text((0, 38), "Joystick: STOP",   fill="white")
#                         draw.line([(0, 54), (W - 1, 54)],     fill="white")
#                         draw.text((0, 56), "Click para detener", fill="white")
#                 time.sleep(0.4)
#                 i += 1
#         threading.Thread(target=_pulse, daemon=True).start()

#     def stop_running(self):
#         self.active_mod = None
#         time.sleep(0.1)
#         self.draw_menu()
#         if self.bus:
#             self.bus.publish("oled:stop", {})

#     def show_alert(self, message: str, module: str, level: str = "critical"):
#         with self.lock:
#             with canvas(self.device) as draw:
#                 draw.rectangle([(0, 0), (W - 1, H - 1)], outline="white")
#                 draw.rectangle([(2, 2), (W - 3, H - 3)], outline="white")
#                 tag = "!! ALERTA !!" if level == "critical" else "! AVISO !"
#                 draw.text((20, 5),  tag,             fill="white")
#                 draw.line([(2, 15), (W - 3, 15)],    fill="white")
#                 draw.text((2, 18),  message[:21],     fill="white")
#                 draw.text((2, 28),  message[21:42],   fill="white")
#                 draw.line([(2, 40), (W - 3, 40)],    fill="white")
#                 draw.text((2, 43),  f"MOD: {module}", fill="white")
#                 draw.text((2, 53),  "Click = ACK",   fill="white")

#     def show_status(self, cpu=0, ram=0, temp=0, ip=""):
#         with self.lock:
#             with canvas(self.device) as draw:
#                 draw.text((22, 0),  "[ ESTADO ]",     fill="white")
#                 draw.line([(0, 9), (W - 1, 9)],       fill="white")
#                 draw.text((0, 12), f"CPU: {cpu}%  {temp:.1f}C", fill="white")
#                 draw.text((0, 22), f"RAM: {ram}%",    fill="white")
#                 draw.text((0, 32), f"IP: {ip}",       fill="white")
#                 draw.line([(0, 43), (W - 1, 43)],     fill="white")
#                 draw.text((0, 46), "WiFi BLE RFID nRF", fill="white")
#                 draw.text((0, 56), "Click = Volver",  fill="white")

#     def cleanup(self):
#         self.device.cleanup()

# import time
# import threading
# from PIL import Image, ImageDraw, ImageFont
# import adafruit_ssd1306

# W, H = 128, 64


# class OledDisplay:
#     def __init__(self, event_bus, i2c_lock, i2c_bus):
#         self.bus = event_bus
#         self.lock = i2c_lock

#         self.device = adafruit_ssd1306.SSD1306_I2C(W, H, i2c_bus)

#         self.image = Image.new("1", (W, H))
#         self.draw = ImageDraw.Draw(self.image)

#         self.current_menu = "root"
#         self.cursor = 0

#         if self.bus:
#             self.bus.subscribe("nav:up", lambda _: self.nav_up())
#             self.bus.subscribe("nav:down", lambda _: self.nav_down())
#             self.bus.subscribe("nav:left", lambda _: self.nav_back())
#             self.bus.subscribe("nav:select", lambda _: self.nav_select())

#     def _render(self):
#         self.device.image(self.image)
#         self.device.show()

#     def clear(self):
#         self.draw.rectangle((0, 0, W, H), outline=0, fill=0)

#     def show_boot(self):
#         with self.lock:
#             self.clear()
#             self.draw.text((20, 20), "SENTINEL", fill=255)
#             self.draw.text((20, 35), "PHANTOM", fill=255)
#             self._render()
#         time.sleep(1.5)

#     def draw_menu(self):
#         with self.lock:
#             self.clear()

#             self.draw.text((0, 0), "MENU", fill=255)
#             self.draw.text((0, 20), "> DEFENSA", fill=255)
#             self.draw.text((0, 30), "  ATAQUE", fill=255)
#             self.draw.text((0, 40), "  ESTADO", fill=255)

#             self._render()

#     def nav_up(self):
#         pass

#     def nav_down(self):
#         pass

#     def nav_select(self):
#         pass

#     def nav_back(self):
#         pass

#     def show_alert(self, message, module, level="info"):
#         with self.lock:
#             self.clear()
#             self.draw.text((0, 0), "ALERTA", fill=255)
#             self.draw.text((0, 20), message[:20], fill=255)
#             self._render()


import time
import threading
from PIL import Image, ImageDraw
import adafruit_ssd1306

W, H = 128, 64


class OledDisplay:
    def __init__(self, event_bus, i2c_lock, i2c_bus):
        self.bus = event_bus
        self.lock = i2c_lock

        self.device = adafruit_ssd1306.SSD1306_I2C(W, H, i2c_bus)

        self.image = Image.new("1", (W, H))
        self.draw = ImageDraw.Draw(self.image)

        self.current_menu = "root"
        self.cursor = 0

        # Suscripción a eventos del joystick
        if self.bus:
            self.bus.subscribe("nav:up", lambda _: self.nav_up())
            self.bus.subscribe("nav:down", lambda _: self.nav_down())
            self.bus.subscribe("nav:left", lambda _: self.nav_back())
            self.bus.subscribe("nav:select", lambda _: self.nav_select())

    def _render(self):
        self.device.image(self.image)
        self.device.show()

    def clear(self):
        self.draw.rectangle((0, 0, W, H), outline=0, fill=0)

    # ── BOOT ─────────────────────────────
    def show_boot(self):
        with self.lock:
            self.clear()
            self.draw.text((20, 20), "SENTINEL", fill=255)
            self.draw.text((20, 35), "PHANTOM", fill=255)
            self._render()
        time.sleep(1.5)

    # ── MENÚ SIMPLE (puedes expandir luego) ─────────────────
    def draw_menu(self):
        with self.lock:
            self.clear()

            items = ["DEFENSA", "ATAQUE", "ESTADO"]

            for i, item in enumerate(items):
                prefix = ">" if i == self.cursor else " "
                self.draw.text((0, 15 + i * 12), f"{prefix} {item}", fill=255)

            self._render()

    # ── NAVEGACIÓN ───────────────────────
    def nav_up(self):
        self.cursor = (self.cursor - 1) % 3
        self.draw_menu()

    def nav_down(self):
        self.cursor = (self.cursor + 1) % 3
        self.draw_menu()

    def nav_select(self):
        self.show_alert(f"Seleccionado {self.cursor}", "SYSTEM")

    def nav_back(self):
        self.draw_menu()

    # ── ALERTAS ──────────────────────────
    def show_alert(self, message, module, level="info"):
        with self.lock:
            self.clear()
            self.draw.text((0, 0), "ALERTA", fill=255)
            self.draw.text((0, 20), message[:20], fill=255)
            self.draw.text((0, 40), f"{module}", fill=255)
            self._render()

    def cleanup(self):
        self.device.fill(0)
        self.device.show()