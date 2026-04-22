import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.rfid.reader import RFIDReader

def run():
    reader = RFIDReader()
    print("--- [PHANTOM WIPER] ---")
    print("Estado: Esperando tarjeta para FORMATEAR...")

    while True:
        res = reader.read_once()
        if res:
            uid = res['uid']
            print(f" [+] Tarjeta detectada: {uid}")
            print(f" [!] Borrando datos del Bloque 4...")
            
            # Escribimos 16 ceros (formato hex)
            resp = reader.send_command("WRITE 4 0000000000000000")
            
            if resp and resp.get("event") == "WRITE_OK":
                print(" ✨ LIMPIEZA COMPLETADA: La tarjeta vuelve a ser una tarjeta común.")
            else:
                print(" ❌ ERROR: No se pudo limpiar la tarjeta.")
            break
        time.sleep(0.1)

if __name__ == "__main__":
    run()
