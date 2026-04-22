import serial
import time
import json

PORT = "COM3"
BAUD = 115200

class PhantomCloner:
    def __init__(self):
        try:
            self.ser = serial.Serial(PORT, BAUD, timeout=2)
            print(f"Conectando a {PORT}...")
            time.sleep(2)
            self.ser.reset_input_buffer()
        except Exception as e:
            print(f"Error de conexión: {e}")
            exit()

    def send_command(self, cmd):
        """Envía un comando y filtra la respuesta para encontrar el JSON."""
        self.ser.write(f"{cmd}\n".encode())
        start_time = time.time()
        
        while (time.time() - start_time) < 3:
            if self.ser.in_waiting:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith('{'):
                    try:
                        return json.loads(line)
                    except:
                        continue
        return {"error": "Timeout o respuesta inválida"}

    def scan_card(self, prompt):
        print(f"\n[PHANTOM] {prompt}")
        while True:
            res = self.send_command("SCAN")
            if "uid" in res:
                print(f"Tarjeta detectada: {res['uid']}")
                return res['uid']
            time.sleep(0.5)

    def run(self):
        print("="*40)
        print("   CENTINEL PHANTOM: CLONADOR TÁCTICO   ")
        print("="*40)

        # 1. FASE DE LECTURA (Tarjeta A)
        uid_origen = self.scan_card("Acerca la TARJETA ORIGEN (A) para copiar...")
        
        bloques_interes = [4, 5, 6]
        buffer_datos = {}

        print("\nCopiando sectores de memoria...")
        for b in bloques_interes:
            res = self.send_command(f"READ:{b}")
            if res.get("status") == "READ_OK":
                buffer_datos[b] = res["data"]
                print(f"  Bloque {b}: [COPIADO]")
            else:
                print(f"  Bloque {b}: [FALLO] - Abortando proceso.")
                return

        # 2. FASE DE TRANSICIÓN
        print("\n" + "!"*45)
        print("!!! RETIRA LA TARJETA ORIGEN AHORA !!!")
        print("!"*45)
        time.sleep(4) # Tiempo para que el usuario cambie la tarjeta

        # 3. FASE DE ESCRITURA (Tarjeta B)
        uid_destino = self.scan_card("Acerca la TARJETA DESTINO (B) para clonar...")

        if uid_destino == uid_origen:
            print("\n[!] ERROR: Es la misma tarjeta. Abortando para evitar bucles.")
            return

        print(f"\nIniciando inyección de datos en {uid_destino}...")
        errores = 0
        for b, hex_data in buffer_datos.items():
            res = self.send_command(f"WRITE:{b}:{hex_data}")
            if res.get("status") == "WRITE_OK":
                print(f"  Bloque {b}: [ESCRITO OK]")
            else:
                print(f"  Bloque {b}: [ERROR DE ESCRITURA]")
                errores += 1

        if errores == 0:
            print("\n" + "*"*40)
            print("   CLONADO EXITOSO - TARJETA LISTA")
            print("*"*40)
        else:
            print(f"\n[!] Clonado incompleto. {errores} bloques fallaron.")

if __name__ == "__main__":
    cloner = PhantomCloner()
    try:
        cloner.run()
    except KeyboardInterrupt:
        print("\nOperación cancelada.")