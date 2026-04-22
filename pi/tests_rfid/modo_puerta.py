import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.rfid.reader import RFIDReader

def run():
    reader = RFIDReader()
    print("--- [PHANTOM DOOR SIMULATOR] ---")
    print("Estado: Sistema de seguridad activo. Presente su credencial...")

    while True:
        res = reader.read_once()
        if res:
            uid = res['uid']
            print(f"\n[SCAN] UID: {uid}")
            
            # Verificación de nivel 2: El código secreto
            print(" [?] Verificando integridad de datos...")
            resp = reader.send_command("READ 4")
            firma = resp.get("content", "").strip() if resp else ""

            if "PHANTOM_SIG_2026" in firma:
                print(" ✅ [ACCESO CONCEDIDO]: Bienvenido, Operador.")
            else:
                print(" 🚨 [ACCESO DENEGADO]: CLON DETECTADO O TARJETA SIN FIRMA.")
                print(f"    Firma leída: '{firma}'")
            
            print("---------------------------------------")
            time.sleep(2) # Pausa para no leer la misma tarjeta mil veces
        time.sleep(0.1)

if __name__ == "__main__":
    run()
