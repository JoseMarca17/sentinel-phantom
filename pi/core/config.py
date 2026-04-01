# pi/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Red
    WIFI_INTERFACE      = os.getenv("WIFI_INTERFACE", "wlan1")
    MONITOR_INTERFACE   = os.getenv("MONITOR_INTERFACE", "wlan1mon")
    UART_PORT           = os.getenv("UART_PORT", "/dev/ttyUSB0")

    # Flask
    FLASK_PORT          = int(os.getenv("FLASK_PORT", 5000))
    FLASK_DEBUG         = os.getenv("FLASK_DEBUG", "False") == "True"

    # Base de datos
    DB_LOCAL_PATH       = os.getenv("DB_LOCAL_PATH", "database/centinela.db")
    DB_POSTGRES_URL     = os.getenv("DB_POSTGRES_URL", "")

    # Sistema
    LOG_LEVEL           = os.getenv("LOG_LEVEL", "INFO")

    # Módulos habilitados — puedes deshabilitar los que no están listos
    MODULES_ENABLED = {
        "wifi":      os.getenv("MODULE_WIFI", "true")      == "true",
        "bluetooth": os.getenv("MODULE_BT", "true")        == "true",
        "rfid":      os.getenv("MODULE_RFID", "false")     == "true",
        "tscm":      os.getenv("MODULE_TSCM", "false")     == "true",
        "ir":        os.getenv("MODULE_IR", "false")       == "true",
        "nrf24":     os.getenv("MODULE_NRF24", "false")    == "true",
    }

config = Config()