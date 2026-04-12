import platform

# Detecta si estás en la laptop o en la Raspberry Pi 3B
DEBUG_MODE = platform.system() != "Linux" or platform.machine() not in ["armv7l", "aarch64"]

# Configuración de Base de Datos local
DB_PATH = "database/sentinel.db"

# --- NUEVAS VARIABLES PARA LA API ---
SERVER_HOST = "0.0.0.0"  # Permite conexiones desde cualquier IP (útil para el celular)
SERVER_PORT = 5000       # Puerto estándar de Flask

# URL de la Laptop (Centro de Mando) para sincronización
SERVER_LAPTOP_URL = "http://192.168.1.100:8000" 

# Parámetros tácticos
NFC_SCAN_INTERVAL = 0.5