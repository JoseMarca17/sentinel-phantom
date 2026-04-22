import serial
import time
import json

PORT = "COM3"
BAUD = 115200

class CentinelValidator:
    def __init__(self):
        try:
            self.ser = serial.Serial(PORT, BAUD, timeout=1)
            print("Iniciando Monitor de Seguridad...")
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            exit()

    def secure_read(self, block_num):
        """Limpia el buffer y solicita una lectura limpia."""
        self.ser.reset_input_buffer()
        self.ser.write(f"READ:{block_num}\n".encode())
        
        # Esperar respuesta válida (saltando ruido)
        start = time.time()
        while (time.time() - start) < 2:
            if self.ser.in_waiting:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith('{'):
                    try:
                        return json.loads(line)
                    except:
                        continue
        return None

    def validate_loop(self):
        print("\n" + "="*40)
        print("   CENTINEL PHANTOM: ACCESS CONTROL   ")
        print("="*40)
        print("Estado: VIGILANDO...")

        SECRET_KEY = "43454E54494E454C5048414E544F4D31"

        try:
            while True:
                # El validador intenta leer el bloque 4 constantemente
                res = self.secure_read(4)
                
                if res and "data" in res:
                    uid = res.get("uid", "N/A")
                    data_hex = res["data"].upper()

                    if data_hex == SECRET_KEY:
                        print(f"\n[✔] {time.strftime('%H:%M:%S')} - ACCESO CONCEDIDO")
                        print(f"    UID: {uid} | FIRMA: VALIDA")
                        # Aquí podrías mandar un comando al ESP32 para prender un LED verde
                    else:
                        print(f"\n[✘] {time.strftime('%H:%M:%S')} - INTRUSO DETECTADO")
                        print(f"    UID: {uid} | FIRMA: CORRUPTA/INVALIDA")
                    
                    print("\nEsperando nueva tarjeta...")
                    time.sleep(2) # Pausa para evitar lecturas repetidas
                
                time.sleep(0.3)
        except KeyboardInterrupt:
            print("\nSistema apagado.")
        finally:
            self.ser.close()

if __name__ == "__main__":
    v = CentinelValidator()
    v.validate_loop()