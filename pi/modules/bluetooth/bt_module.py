import asyncio
from modules.bluethooth.scanner import BLEScanner
from modules.bluethooth.attacker import BLEAttacker

class BluetoothModule:
    def __init__(self):
        self.scanner = BLEScanner()
        self.attacker = BLEAttacker()
        self.running = False

    def start(self):
        print("[*] Modulo Bluetooth iniciado")
        self.running = True

    def stop(self):
        print("[*] Modulo Bluetooth detenido")
        self.running = False

    def status(self):
        return {"running": self.running}

    async def run_scan(self, duration=10):
        await self.scanner.scan(duration)

    def disconnect(self, target_mac: str):
        return self.attacker.disconnect_device(target_mac)

    def spoof(self, fake_name: str):
        self.attacker.spoof_name(fake_name)

if __name__ == "__main__":
    bt = BluetoothModule()
    bt.start()
    asyncio.run(bt.run_scan())
    bt.stop()
