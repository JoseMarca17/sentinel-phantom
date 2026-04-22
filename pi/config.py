"""
SENTINEL PHANTOM - Configuración Central
Escuela Militar de Ingeniería (EMI) - Open House 2026
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Identidad del dispositivo ───────────────────────────────────────────────
DEVICE_ID   = os.getenv("DEVICE_ID", "PHANTOM-PI-01")
DEVICE_NAME = os.getenv("DEVICE_NAME", "Sentinel Phantom Unit 1")

# ─── API Flask (Pi local) ─────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 5000))
API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "phantom-secret-2026")

# ─── Base de datos local (SQLite) ─────────────────────────────────────────────
DB_PATH = os.getenv("DB_PATH", "/home/phantom/centinel-phantom/pi/database/phantom.db")

# ─── Servidor central (SQL Server en laptop) ──────────────────────────────────
SERVER_URL       = os.getenv("SERVER_URL", "http://192.168.1.100:8000")
SERVER_API_KEY   = os.getenv("SERVER_API_KEY", "")
SYNC_INTERVAL_S  = int(os.getenv("SYNC_INTERVAL_S", 60))   # segundos entre sincronizaciones

# ─── Hardware serial ─────────────────────────────────────────────────────────
ESP32_PORT  = os.getenv("ESP32_PORT", "/dev/ttyUSB0")
ESP32_BAUD  = int(os.getenv("ESP32_BAUD", 115200))
PICO_PORT   = os.getenv("PICO_PORT", "/dev/ttyUSB1")
PICO_BAUD   = int(os.getenv("PICO_BAUD", 115200))

# ─── Interfaz WiFi monitor ────────────────────────────────────────────────────
WIFI_IFACE_MONITOR = os.getenv("WIFI_IFACE_MONITOR", "wlan1")
WIFI_IFACE_AP      = os.getenv("WIFI_IFACE_AP",      "wlan0")

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE  = os.getenv("LOG_FILE",  "/home/phantom/centinel-phantom/pi/logs/phantom.log")

# ─── Módulos habilitados ──────────────────────────────────────────────────────
MODULES_ENABLED: dict[str, bool] = {
    "wifi":      os.getenv("MOD_WIFI",      "true").lower() == "true",
    "bluetooth": os.getenv("MOD_BLUETOOTH", "true").lower() == "true",
    "rfid":      os.getenv("MOD_RFID",      "true").lower() == "true",
    "tscm":      os.getenv("MOD_TSCM",      "true").lower() == "true",
    "ir":        os.getenv("MOD_IR",        "true").lower() == "true",
    "nrf24":     os.getenv("MOD_NRF24",     "true").lower() == "true",
}

# ─── Severidades de alerta ────────────────────────────────────────────────────
class Severity:
    INFO     = "INFO"
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"

SEVERITY_ORDER = {
    Severity.INFO:     0,
    Severity.LOW:      1,
    Severity.MEDIUM:   2,
    Severity.HIGH:     3,
    Severity.CRITICAL: 4,
}
# ─── OLED Display ─────────────────────────────────────────────────────────────
OLED_ADDRESS = int(os.getenv("OLED_ADDRESS", "0x3C"), 16)

# ─── Objeto config (alias del modulo) ─────────────────────────────────────────
class config:
    DEVICE_ID          = DEVICE_ID
    DEVICE_NAME        = DEVICE_NAME
    API_HOST           = API_HOST
    API_PORT           = API_PORT
    DB_PATH            = DB_PATH
    SERVER_URL         = SERVER_URL
    ESP32_PORT         = ESP32_PORT
    ESP32_BAUD         = ESP32_BAUD
    WIFI_IFACE_MONITOR = WIFI_IFACE_MONITOR
    WIFI_IFACE_AP      = WIFI_IFACE_AP
    LOG_LEVEL          = LOG_LEVEL
    MODULES_ENABLED    = MODULES_ENABLED
    OLED_ADDRESS       = OLED_ADDRESS
