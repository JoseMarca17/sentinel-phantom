import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── General ────────────────────────────────────────────────
    DEBUG       = os.getenv('DEBUG', 'false').lower() == 'true'
    SECRET_KEY  = os.getenv('SECRET_KEY', 'sentinel-phantom-dev-key')

    # ── API Flask (Pi) ─────────────────────────────────────────
    API_HOST    = os.getenv('API_HOST', '0.0.0.0')
    API_PORT    = int(os.getenv('API_PORT', 5000))

    # ── Servidor central (laptop) ──────────────────────────────
    SERVER_URL  = os.getenv('SERVER_URL', 'http://192.168.1.100:5001')
    SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', 30))  # segundos

    # ── Hardware ───────────────────────────────────────────────
    WIFI_IFACE      = os.getenv('WIFI_IFACE', 'wlan1')          # MT7601U
    ESP32_PORT      = os.getenv('ESP32_PORT', '/dev/ttyUSB0')
    ESP32_BAUD      = int(os.getenv('ESP32_BAUD', 115200))
    PICO_PORT       = os.getenv('PICO_PORT', '/dev/ttyACM0')
    PICO_BAUD       = int(os.getenv('PICO_BAUD', 115200))
    I2C_BUS         = int(os.getenv('I2C_BUS', 1))
    OLED_ADDRESS    = int(os.getenv('OLED_ADDRESS', '0x3C'), 16)

    # ── SQLite local ───────────────────────────────────────────
    DB_PATH     = os.getenv('DB_PATH', '/home/pi/sentinel-phantom/data/sentinel.db')

    # ── nRF24 ──────────────────────────────────────────────────
    NRF24_CE_PIN  = int(os.getenv('NRF24_CE_PIN', 25))
    NRF24_CSN_PIN = int(os.getenv('NRF24_CSN_PIN', 8))

config = Config()