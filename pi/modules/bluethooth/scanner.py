import asyncio
from bleak import BleakScanner
from manuf import manuf

class BLEScanner:
    def __init__(self):
        self.devices_found = []
        self.parser = manuf.MacParser()

    def get_vendor(self, mac: str) -> str:
        try:
            vendor = self.parser.get_manuf(mac)
            return vendor if vendor else "Desconocido"
        except:
            return "Desconocido"

    async def scan(self, duration=10):
        print(f"[*] Iniciando escaneo BLE por {duration} segundos...")
        devices = await BleakScanner.discover(timeout=duration)

        if not devices:
            print("[-] No se encontraron dispositivos")
            return

        print(f"[+] {len(devices)} dispositivo(s) encontrado(s):\n")
        for d in devices:
            vendor = self.get_vendor(d.address)
            print(f"  MAC:       {d.address}")
            print(f"  Nombre:    {d.name or 'Desconocido'}")
            print(f"  Fabricante:{vendor}")
            print(f"  -------------------------")
            self.devices_found.append(d)

if __name__ == "__main__":
    scanner = BLEScanner()
    asyncio.run(scanner.scan())
