import asyncio
from bleak import BleakScanner

class BLEScanner:
    def __init__(self):
        self.devices_found = []

    async def scan(self, duration=10):
        print(f"[*] Iniciando escaneo BLE por {duration} segundos...")
        devices = await BleakScanner.discover(timeout=duration)
        
        if not devices:
            print("[-] No se encontraron dispositivos")
            return
        
        print(f"[+] {len(devices)} dispositivo(s) encontrado(s):\n")
        for d in devices:
            print(f"  MAC:    {d.address}")
            print(f"  Nombre: {d.name or 'Desconocido'}")
            print(f"  RSSI:   {d.details} ")
            print(f"  -------------------------")
            self.devices_found.append(d)

if __name__ == "__main__":
    scanner = BLEScanner()
    asyncio.run(scanner.scan(duration=30))
