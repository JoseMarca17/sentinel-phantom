import serial
import time
import json

PORT = "COM3"
BAUD = 115200

def run_injector():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=2)
        print(f"Conectado a {PORT}. Esperando booteo...")
        time.sleep(2)
        ser.reset_input_buffer()

        # Firma secreta de CENTINEL PHANTOM
        mock_data = {
            "4": "43454E54494E454C5048414E544F4D31", # "CENTINELPHANTOM1"
            "5": "4F50454E20484F55534520454D492032", # "OPEN HOUSE EMI 2"
            "6": "000000000000000000000000000000FF"
        }

        print("\n--- INYECTOR TÁCTICO PHANTOM ---")
        print("Acerca la TARJETA ORIGEN ahora...")

        for block, hex_val in mock_data.items():
            success = False
            attempts = 0
            while not success and attempts < 3:
                attempts += 1
                print(f"Escribiendo bloque {block} (Intento {attempts})...", end="\r")
                
                ser.write(f"WRITE:{block}:{hex_val}\n".encode())
                time.sleep(0.8) # Tiempo para escritura en EEPROM
                
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if "WRITE_OK" in line:
                    print(f"Bloque {block}: [OK]                     ")
                    success = True
                else:
                    time.sleep(0.5)
            
            if not success:
                print(f"\n[!] Error crítico en bloque {block}. Revisa cables.")
                break

        ser.close()
        print("\nInyección finalizada con éxito.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    run_injector()