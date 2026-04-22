import sys
import os
import time

# Parche de ruta para encontrar el módulo reader
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.rfid.reader import RFIDReader

def run():
    reader = RFIDReader()
    print("--- [PHANTOM ENROLLER] ---")
    print("Estado: Esperando tarjeta para grabación...")

    while True:
        res = reader.read_once()
        if res:
            uid = res['uid']
            print(f" [+] Tarjeta detectada: {uid}")
            print(f" [!] Grabando código secreto 'PHANTOM_SIG_2026' en Bloque 4...")
            
            resp = reader.send_command("WRITE 4 PHANTOM_SIG_2026")
            
            if resp and resp.get("event") == "WRITE_OK":
                print(" ✅ ÉXITO: Tarjeta maestra lista. Ya puedes retirarla.")
            else:
                print(f" ❌ ERROR: El ESP32 rechazó la escritura. {resp}")
            break # Termina después de una acción
        time.sleep(0.1)

if __name__ == "__main__":
    run()
