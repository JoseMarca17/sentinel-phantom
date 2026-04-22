import serial
import time
import json

PORT = "COM3"
BAUD = 115200

class PhantomForensics:
    def __init__(self):
        try:
            self.ser = serial.Serial(PORT, BAUD, timeout=1)
            print(f"[*] Conectado a {PORT}. Inicializando...")
            time.sleep(2)
            self.ser.reset_input_buffer()
        except Exception as e:
            print(f"[-] Error de conexión: {e}")
            exit()

    def run_analysis(self):
        print("\n" + "="*45)
        print("   CENTINEL PHANTOM: ANALIZADOR DE HARDWARE   ")
        print("="*45)
        print("Esperando tarjeta para auditoría...")

        while True:
            try:
                # Pedir escaneo al ESP32
                self.ser.write(b"SCAN\n")
                
                # Leer respuesta
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                
                if line.startswith('{'):
                    res = json.loads(line)
                    
                    # Validar que realmente se detectó una tarjeta
                    if res.get("status") == "OK" and "uid" in res:
                        uid = res["uid"].upper()
                        is_clone = res.get("is_clone", False)

                        print(f"\n[+] TARJETA DETECTADA: {uid}")
                        print(f"[*] Análisis de fabricante: ", end="")
                        
                        if is_clone:
                            print("⚠️  CLON DETECTADO (Gen1 Magic)")
                            print("    RIESGO: Muy Alto. El UID puede ser suplantado fácilmente.")
                        else:
                            print("🛡️  ORIGINAL / NO-MAGIC")
                            print("    RIESGO: Bajo. No responde a comandos de clonación estándar.")
                        
                        print("-" * 45)
                        time.sleep(2) # Pausa para que el usuario retire la tarjeta
                    
                # Si no hay tarjeta o hay error, no imprimimos nada para no llenar la pantalla
                time.sleep(0.4)

            except KeyboardInterrupt:
                print("\n[*] Auditoría finalizada por el usuario.")
                break
            except Exception as e:
                print(f"\n[!] Error en loop: {e}")
                break

        self.ser.close()

if __name__ == "__main__":
    audit = PhantomForensics()
    audit.run_analysis()