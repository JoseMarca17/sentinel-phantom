class WPSScanner:
    def scan_wps(self, interface="wlan0mon"):
        # Llama a wash para listar redes con WPS
        cmd = ["sudo", "wash", "-i", interface]
        subprocess.run(cmd)