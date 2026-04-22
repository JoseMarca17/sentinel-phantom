import serial
import time
import json

PORT = "COM3" 
BAUD = 115200

def send_cmd(ser, cmd):
    ser.write(f"{cmd}\n".encode())
    time.sleep(0.4) # Un poco más de margen por si el I2C es lento
    responses = []
    while ser.in_waiting:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith('{'): # SOLO procesar si parece JSON
            try:
                responses.append(json.loads(line))
            except:
                pass
        else:
            print(f"INFO: {line}") # Mostrar logs que no son JSON
    return responses

def main():
    try:
        print(f"Conectando a {PORT}...")
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2) 
        ser.reset_input_buffer() # Limpiar mensajes de inicio

        print("\n=== TEST 1: PING/STATUS ===")
        # Probamos el comando STATUS que ya vimos que responde
        r = send_cmd(ser, "STATUS")
        print(f"Respuesta: {r}")

        print("\n=== TEST 2: SIMULAR AUTORIZADO ===")
        print("Enviando UID que debería estar en tu whitelist...")
        # Cambia 'DEADBEEF' por el UID de tu tarjeta real si ya la conoces
        r = send_cmd(ser, "CHECK:C0EFFB5F") 
        if r and "authorized" in r[0]:
            print(f"Resultado: {'PASS' if r[0]['authorized'] else 'DENEGADO (pero comunicando)'}")

        print("\n=== TEST 3: LECTURA FÍSICA ===")
        print("Tienes 10 segundos para acercar tu tarjeta al PN532...")
        ser.timeout = 10
        start_time = time.time()
        while time.time() - start_time < 10:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith('{'):
                    data = json.loads(line)
                    print(f"\n¡EXITO! Tarjeta: {data['uid']} | Fuente: {data['source']}")
                    break
        else:
            print("\nTimeout: No se detectó tarjeta.")

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        ser.close()
        print("\nPrueba terminada.")

main()