import serial
import json
import time
import threading
import glob
import sys

# ── Búsqueda inteligente del puerto ───────────────────────────────
def find_pico_port() -> str:
    """Busca el Pico W priorizando dispositivos conocidos."""
    # Priorizar ACM (típico de Pico) sobre USB (adaptadores genéricos)
    candidates = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
    if not candidates:
        return None
    return candidates[0]

# ── Comunicación serial mejorada ──────────────────────────────────
class PicoComm:
    def __init__(self, port: str):
        self.port = port
        try:
            # Añadimos un timeout corto para no bloquear el hilo principal
            self.ser = serial.Serial(port, 115200, timeout=0.1)
        except Exception as e:
            print(f"  [!] Error fatal abriendo puerto: {e}")
            sys.exit(1)
            
        time.sleep(2)  # El Pico W suele resetearse al abrir el puerto
        self.running = True
        self._t = threading.Thread(target=self._reader, daemon=True)
        self._t.start()

    def send(self, cmd: str, params: dict = None):
        """Envía comandos en formato JSON."""
        try:
            payload = {"cmd": cmd, "params": params or {}}
            msg = json.dumps(payload) + "\n"
            self.ser.write(msg.encode('utf-8'))
            self.ser.flush() # Forzar el envío
        except Exception as e:
            print(f"  [!] Error al enviar: {e}")

    def _reader(self):
        """Hilo de lectura con manejo de errores de JSON."""
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    
                    # Intentar parsear como JSON, si falla es un print de debug del Pico
                    try:
                        msg = json.loads(line)
                        self._handle(msg)
                    except json.JSONDecodeError:
                        if line: # No imprimir líneas vacías
                            print(f"  [Pico LOG] {line}")
            except Exception as e:
                if self.running:
                    print(f"  [!] Error en hilo lector: {e}")
                break
            time.sleep(0.01) # Evitar saturar la CPU

    def _handle(self, msg: dict):
        """Procesa los eventos entrantes."""
        event = msg.get("event", "unknown")
        data  = msg.get("data", {})
        
        # Diccionario de eventos para evitar tantos if/else (más limpio)
        handlers = {
            "ap_up": lambda d: print(f"\n[+] AP ACTIVO: {d.get('ssid')} | IP: {d.get('ip')} | Canal: {d.get('channel')}"),
            "ap_down": lambda d: print("\n[-] AP detenido."),
            "client_join": lambda d: print(f"\n[!] VÍCTIMA CONECTADA: {d.get('mac')} (Total: {d.get('total')})"),
            "client_leave": lambda d: print(f"\n[-] Cliente desconectado: {d.get('mac')}"),
            "status": lambda d: print(f"\n[STATUS] FW: {d.get('fw')} | AP: {d.get('ap_active')} | Clientes: {d.get('count', 0)}"),
            "pong": lambda d: print(f"  [PONG] Respuesta del FW: {d.get('fw')}"),
            "ack": lambda d: None, # Silencioso para no ensuciar
            "error": lambda d: print(f"\n  [ERROR PICO] {d.get('msg')}")
        }
        
        handler = handlers.get(event)
        if handler:
            handler(data)
        else:
            print(f"  [?] Evento desconocido: {msg}")

    def close(self):
        self.running = False
        self.ser.close()

# ── Lógica de Menú ────────────────────────────────────────────────
def menu(pico: PicoComm):
    print("\n" + "="*40)
    print("      SENTINEL PHANTOM - TEST MODE")
    print("="*40)

    while True:
        print("\n1. Start Open AP     2. Start WPA2 AP")
        print("3. Pico Status       4. Stop AP")
        print("5. Ping              6. Exit")
        
        try:
            op = input("\n> Selecciona opción: ").strip()
        except EOFError: break

        if op == "1":
            ssid = input("SSID a suplantar: ") or "WiFi_Gratis"
            pico.send("start", {"ssid": ssid, "password": "", "channel": 6})
        elif op == "2":
            ssid = input("SSID a suplantar: ")
            pwd = input("Password (min 8): ")
            if len(pwd) < 8:
                print("Error: Contraseña muy corta.")
                continue
            pico.send("start", {"ssid": ssid, "password": pwd, "channel": 1})
        elif op == "3":
            pico.send("status")
        elif op == "4":
            pico.send("stop")
        elif op == "5":
            pico.send("ping")
        elif op == "6":
            pico.send("stop")
            time.sleep(0.2)
            break
        else:
            print("Opción inválida.")

def main():
    port = find_pico_port()
    if not port:
        print("[-] Pico W no detectado. Revisa la conexión USB.")
        return

    print(f"[*] Conectando a {port}...")
    pico = PicoComm(port)
    
    try:
        pico.send("ping")
        menu(pico)
    except KeyboardInterrupt:
        print("\n[*] Abortado por el usuario.")
    finally:
        pico.close()
        print("[*] Conexión cerrada.")

if __name__ == "__main__":
    main()
