import serial
import time
import json

PORT = "COM3"
BAUD = 115200

class PhantomWiper:
    def __init__(self):
        try:
            self.ser = serial.Serial(PORT, BAUD, timeout=2)
            time.sleep(2)
            self.ser.reset_input_buffer()
        except Exception as e:
            print(f"Error: {e}")
            exit()

    def wipe(self):
        print("\n" + "="*40)
        print("   CENTINEL PHANTOM: WIPER TOOL   ")
        print("="*40)
        print("Acerca la tarjeta que deseas RESETEAR...")

        # 1. Esperar tarjeta
        uid = ""
        while not uid:
            self.ser.write(b"SCAN\n")
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith('{'):
                res = json.loads(line)
                if res.get("status") == "OK":
                    uid = res["uid"]
        
        print(f"[*] Tarjeta detectada: {uid}")
        confirm = input(f"¿Estás seguro de resetear los sectores 1 y 2? (s/n): ")
        if confirm.lower() != 's': return

        # Bloques de datos a limpiar (Sector 1 y 2)
        # No tocamos los trailers (3, 7, 11) para evitar bloqueos
        bloques_limpiar = [4, 5, 6, 8, 9, 10]
        data_reset = "00000000000000000000000000000000"

        for b in bloques_limpiar:
            print(f"Limpiando bloque {b}...", end="\r")
            self.ser.write(f"WRITE:{b}:{data_reset}\n".encode())
            time.sleep(0.6)
            res = self.ser.readline().decode('utf-8', errors='ignore').strip()
            
            if "WRITE_OK" in res:
                print(f"Bloque {b}: [LIMPIO]               ")
            else:
                print(f"Bloque {b}: [ERROR]                 ")

        print("\n[✔] Proceso de limpieza finalizado.")
        self.ser.close()

if __name__ == "__main__":
    wiper = PhantomWiper()
    wiper.wipe()