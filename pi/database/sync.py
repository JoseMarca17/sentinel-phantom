# pi/database/sync.py
import sqlite3
import requests
from config import SERVER_LAPTOP_URL

def sync_to_server():
    """Sincroniza logs locales con el servidor central de la laptop."""
    try:
        conn = sqlite3.connect('database/sentinel.db')
        cursor = conn.cursor()
        # Seleccionar logs no sincronizados (puedes añadir una columna 'synced')
        logs = cursor.execute("SELECT * FROM logs WHERE synced = 0").fetchall()
        
        for log in logs:
            response = requests.post(f"{SERVER_LAPTOP_URL}/api/history", json=log)
            if response.status_code == 200:
                cursor.execute("UPDATE logs SET synced = 1 WHERE id = ?", (log[0],))
        
        conn.commit()
    except Exception as e:
        print(f"[!] Error de sincronización: {e}")