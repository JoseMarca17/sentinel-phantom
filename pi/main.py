import time
import threading
from core.event_bus import event_bus
from database.local_db import LocalDB
from modules.rfid.rfid_module import RFIDTopModule
from config import DEBUG_MODE, SERVER_HOST, SERVER_PORT
from api.app import start_api
from hardware.esp32_bridge import ESP32Bridge

# Importaremos otros módulos (WiFi, BT, etc.) a medida que se desarrollen
# from modules.wifi.wifi_module import WiFiTopModule

def sentinel_monitor(event_type, data):
    """
    Callback global del EventBus. 
    Actúa como el sistema de registro forense exigido por la EMI.
    """
    db = LocalDB()
    module_name = data.get('module', 'Unknown')
    message = data.get('msg', 'No description')
    
    # Registro en base de datos local (SQLite)
    db.insert_log(module_name, event_type, message)
    
    # Si el evento es CRITICAL, imprimimos con prioridad en consola
    if event_type in ["ALERT", "RFID_DETECTED"]:
        print(f"\n[!] ALERTA DE SEGURIDAD [{event_type}]: {message}")

def main():
    print("="*50)
    print("      SENTINEL PHANTOM - SISTEMA INICIADO")
    print(f"      MODO: {'SIMULACIÓN' if DEBUG_MODE else 'PRODUCCIÓN'}")
    print("="*50)

    # 1. Configurar el Bus de Eventos para monitoreo centralizado
    event_bus.subscribe(sentinel_monitor)

    # 2. Instanciar los Sistemas (Módulos de Nivel Superior)
    # Según el Anexo B, esto unifica capacidades avanzadas en un único dispositivo
    rfid_system = RFIDTopModule()
    # wifi_system = WiFiTopModule() # Futura integración

    # 3. Iniciar hilos de ejecución
    # Cumple con el diseño experimental para manejo de variables simultáneas
    modules = [rfid_system]
    
    for module in modules:
        module.start()
        print(f"[*] Módulo {module.name} cargado y en ejecución.")

    print("\n[+] Sentinel Phantom operando. Presione Ctrl+C para finalizar.")
    
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    print(f"[*] Dashboard API escuchando en {SERVER_HOST}:{SERVER_PORT}")
    bridge = ESP32Bridge(port='/dev/ttyUSB1') 
    bridge.start()
    try:
        while True:
            # El bucle principal se mantiene libre para supervisión global
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Finalizando despliegue táctico...")
        for module in modules:
            module.stop()
        print("[OK] Sistema apagado de forma segura.")

if __name__ == "__main__":
    main()