import asyncio
import board
import busio
import threading

from api.app import run_api

from core.event_bus import bus
from core.logger import get_logger
from hardware.oled_display import OledDisplay
from hardware.joystick import Joystick
from modules.rfid.rfid_module import RFIDModule
from modules.bluethooth.bt_module import BluetoothModule
from modules.nrf.nrf_module import NrfController
from modules.wifi.wifi_module import WifiModule
from api.app import run_api, socketio
import threading
log = get_logger("main")

rfid     = None
bt       = None
nrf      = None
oled     = None
wifi_ids = None
_loop    = None


def handle_oled_action(event):
    action = event["payload"]["action"]
    log.info(f"Acción recibida: {action}")

    # ── RFID ──────────────────────────────────────────────────────────────────
    if action == "clone_rfid":
        if rfid is None:
            log.error("RFID no inicializado")
            return

        future = asyncio.run_coroutine_threadsafe(rfid.clone_card(), _loop)

        def on_done_rfid(f):
            exc = f.exception()
            if exc:
                log.error(f"clone_card() terminó con excepción: {exc}")
            else:
                log.info(f"clone_card() terminó OK: {f.result()}")

        future.add_done_callback(on_done_rfid)

    # ── BLUETOOTH ─────────────────────────────────────────────────────────────
    elif action == "bt_scan":
        if bt is None:
            log.error("Bluetooth no inicializado")
            return

        future = asyncio.run_coroutine_threadsafe(
            bt.run_scan(duration=10), _loop
        )

        def on_done_bt(f):
            exc = f.exception()
            if exc:
                log.error(f"bt_scan() terminó con excepción: {exc}")
            else:
                log.info(f"bt_scan() terminó OK: {f.result()}")

        future.add_done_callback(on_done_bt)

    # ── NRF: escaneo WiFi ─────────────────────────────────────────────────────
    elif action == "nrf_wifi_scan":
        if nrf is None:
            log.error("NRF no inicializado")
            return

        def on_scan_done(networks):
            bus.publish_sync("oled:wifi_nets", {"networks": networks})

        def on_status(msg):
            bus.publish_sync("oled:wifi_status", {"msg": msg})

        nrf.on_scan_done(on_scan_done)
        nrf.on_status(on_status)
        nrf.scan()

    # ── NRF: ataque WiFi ──────────────────────────────────────────────────────
    elif action == "nrf_wifi_attack":
        if nrf is None:
            log.error("NRF no inicializado")
            return

        net_idx = event["payload"].get("net_idx", 0)
        nrf.select(net_idx)
        nrf.start_wifi()

    # ── NRF: BT jam ───────────────────────────────────────────────────────────
    elif action == "nrf_bt":
        if nrf is None:
            log.error("NRF no inicializado")
            return

        def on_status_bt(msg):
            bus.publish_sync("oled:wifi_status", {"msg": msg})

        nrf.on_status(on_status_bt)
        nrf.start_bt()
        bus.publish_sync("oled:bt_active", {})

    elif action == "nrf_stop":
        if nrf is None:
            return
        nrf.stop()
        bus.publish_sync("oled:return_menu", {})

    # ── ESTADO ────────────────────────────────────────────────────────────────
    elif action == "status":
        lines = [
            f"RFID: {'OK' if rfid     else 'X'}",
            f"BT:   {'OK' if bt       else 'X'}",
            f"NRF:  {'OK' if nrf      else 'X'}",
            f"WIFI: {'OK' if wifi_ids else 'X'}",
        ]
        bus.publish_sync("oled:status", {"lines": lines})

    # ── WIFI: todo delegado a WifiModule vía bus ──────────────────────────────
    elif action in (
        "wifi_ids_start",      "wifi_ids_stop",
        "wifi_deauth",         "wifi_do_deauth",
        "wifi_beacon_flood",   "wifi_do_beacon",
        "wifi_evil_twin",
        "wifi_pmkid",          "wifi_do_pmkid",
        "wifi_sniffer_start",  "wifi_sniffer_stop",
        "wifi_sniffer_devices",
    ):
        if wifi_ids is None:
            log.error("Wifi no inicializado")
        # WifiModule está suscrito a oled:action y maneja estas acciones
    # Emitir acción al dashboard
    
    else:
        log.warning(f"Acción desconocida: {action}")
    
    socketio.emit("action", {
        "action": action
    })


async def main():
    global rfid, bt, nrf, oled, wifi_ids, _loop

    _loop = asyncio.get_running_loop()

    log.info("═══ SENTINEL PHANTOM ═══")

    i2c      = busio.I2C(board.SCL, board.SDA)
    i2c_lock = threading.Lock()

    # ── OLED ──────────────────────────────────────────────────────────────────
    try:
        oled = OledDisplay(bus, i2c_lock, i2c)
        oled.show_boot()
        oled.draw_menu()
        log.info("OLED OK")
    except Exception as e:
        log.warning(f"OLED no disponible: {e}")
        oled = None

    # ── JOYSTICK ──────────────────────────────────────────────────────────────
    try:
        joystick = Joystick(bus, i2c_lock, i2c)
        log.info("Joystick OK")
    except Exception as e:
        log.warning(f"Joystick no disponible: {e}")
        joystick = None

    # ── RFID ──────────────────────────────────────────────────────────────────
    try:
        rfid = RFIDModule()
        await rfid.start()
        log.info("RFID OK")
    except Exception as e:
        log.warning(f"RFID no disponible: {e}")
        rfid = None

    # ── BLUETOOTH ─────────────────────────────────────────────────────────────
    try:
        bt = BluetoothModule()
        await bt.start()
        log.info("Bluetooth OK")
    except Exception as e:
        log.warning(f"Bluetooth no disponible: {e}")
        bt = None

    # ── WiFi Module ───────────────────────────────────────────────────────────
    try:
        wifi_ids = WifiModule()
        log.info("WifiModule OK")
    except Exception as e:
        log.warning(f"WifiModule no disponible: {e}")
        wifi_ids = None

    # ── NRF ───────────────────────────────────────────────────────────────────
    try:
        nrf = NrfController(port="/dev/ttyUSB1")
        log.info("NRF OK")
    except Exception as e:
        log.warning(f"NRF no disponible: {e}")
        nrf = None

    bus.subscribe("oled:action", handle_oled_action)

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        log.info("Cerrando...")

        if rfid:
            await rfid.stop()
        if bt:
            await bt.stop()
        if nrf:
            nrf.stop()
        if joystick:
            joystick.stop()
        if oled:
            oled.cleanup()
    # ── API WEB (FLASK + SOCKET.IO) ─────────────────────────────
# ── REGISTRO DE MÓDULOS ──
module_registry = {
    "rfid": rfid,
    "bluetooth": bt,
    "wifi": wifi_ids,
}

# ── INICIAR API ──
api_thread = threading.Thread(
    target=run_api,
    args=(module_registry,),
    daemon=True
)
api_thread.start()

log.info("API + Socket.IO corriendo")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bye")