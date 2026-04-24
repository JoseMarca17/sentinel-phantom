from scapy.all import sniff, ARP, IP, TCP, DNS, DNSQR
from core.event_bus import bus
from core.logger import get_logger
import subprocess
import threading
import time

from api.app import socketio

log = get_logger("wifi.sniffer")


class NetworkSniffer:

    def __init__(self, interface="wlan1"):
        self.interface = interface
        self.running   = False
        self._thread   = None
        self._devices  = {}
        self._hopper   = None

    # ─────────────────────────────────────────
    # MODO MONITOR
    # ─────────────────────────────────────────

    def _set_monitor(self):
        log.info("Modo monitor ON")

        subprocess.run(["sudo", "ip", "link", "set", self.interface, "down"])
        subprocess.run(["sudo", "iw", self.interface, "set", "monitor", "control"])
        subprocess.run(["sudo", "ip", "link", "set", self.interface, "up"])
        time.sleep(1)

    def _set_managed(self):
        log.info("Modo managed ON")

        subprocess.run(["sudo", "ip", "link", "set", self.interface, "down"])
        subprocess.run(["sudo", "iw", self.interface, "set", "type", "managed"])
        subprocess.run(["sudo", "ip", "link", "set", self.interface, "up"])
        time.sleep(1)

    # ─────────────────────────────────────────
    # CHANNEL HOPPING
    # ─────────────────────────────────────────

    def _channel_hopper(self):
        channels = list(range(1, 14))

        while self.running:
            for ch in channels:
                subprocess.run(
                    ["sudo", "iw", "dev", self.interface, "set", "channel", str(ch)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(0.4)

                if not self.running:
                    break

    # ─────────────────────────────────────────
    # START / STOP
    # ─────────────────────────────────────────

    def start(self, duration: int = 30):
        if self.running:
            log.warning("Sniffer ya activo")
            return

        self._devices = {}
        self.running  = True

        # OLED inicio
        bus.publish_sync("oled:wifi_status", {"msg": "Sniffer ON"})

        self._set_monitor()

        # iniciar channel hopping
        self._hopper = threading.Thread(target=self._channel_hopper, daemon=True)
        self._hopper.start()

        self._thread = threading.Thread(
            target=self._run,
            args=(duration,),
            daemon=True
        )
        self._thread.start()

        log.info(f"Sniffer iniciado en {self.interface}")

    def stop(self):
        self.running = False
        log.info("Sniffer detenido")

    # ─────────────────────────────────────────
    # LOOP PRINCIPAL
    # ─────────────────────────────────────────

    def _run(self, duration: int):
        try:
            start_time = time.time()

            while self.running and (time.time() - start_time) < duration:

                sniff(
                    iface=self.interface,
                    prn=self._process_packet,
                    store=False,
                    timeout=2,
                )

                # 🔥 enviar dispositivos SIEMPRE (OLED live)
                bus.publish_sync("oled:sniffer_devices", {
                    "devices": list(self._devices.values())
                })

                # progreso
                elapsed = int(time.time() - start_time)

                bus.publish_sync("oled:sniffer_progress", {
                    "devices": list(self._devices.values()),
                    "elapsed": elapsed,
                    "total": duration
                })

            self.running = False

            devs = list(self._devices.values())
            log.info(f"Dispositivos: {len(devs)}")

            bus.publish_sync("wifi.devices", {"devices": devs})

            if not devs:
                bus.publish_sync("oled:wifi_status", {"msg": "0 dispositivos"})
                time.sleep(1.5)

        except Exception as e:
            log.error(f"Sniffer error: {e}")
            bus.publish_sync("oled:wifi_status", {"msg": "Error sniffer"})

        finally:
            self._set_managed()
            bus.publish_sync("oled:return_menu", {})

    # ─────────────────────────────────────────
    # PROCESADO DE PAQUETES
    # ─────────────────────────────────────────

    def _process_packet(self, pkt):
        try:
            # ── ARP → detectar dispositivos
            if pkt.haslayer(ARP):
                ip  = pkt[ARP].psrc
                mac = pkt[ARP].hwsrc

                if ip == "0.0.0.0" or mac == "ff:ff:ff:ff:ff:ff":
                    return

                if mac not in self._devices:
                    self._devices[mac] = {
                        "ip": ip,
                        "mac": mac,
                        "activity": []
                    }

                    log.info(f"Nuevo dispositivo: {ip} ({mac})")

                    # OLED feedback inmediato
                    bus.publish_sync("oled:wifi_status", {
                        "msg": f"{len(self._devices)} dev"
                    })

            # ── DNS → dominios
            if pkt.haslayer(DNS) and pkt.haslayer(DNSQR):
                if pkt[DNS].qr == 0:

                    domain = pkt[DNSQR].qname.decode(errors="ignore").rstrip(".")
                    src_ip = pkt[IP].src if pkt.haslayer(IP) else None

                    if src_ip and domain:
                        log.info(f"DNS: {src_ip} → {domain}")

                        for dev in self._devices.values():
                            if dev["ip"] == src_ip:
                                dev["activity"].append(domain)
                                dev["activity"] = dev["activity"][-10:]

                                # OLED mostrar dominio
                                bus.publish_sync("oled:wifi_status", {
                                    "msg": domain[:20]
                                })

            # ── TCP (HTTP / HTTPS)
            if pkt.haslayer(TCP) and pkt.haslayer(IP):
                src = pkt[IP].src
                dst = pkt[IP].dst

                if pkt[TCP].dport in [80, 443]:
                    for dev in self._devices.values():
                        if dev["ip"] == src:
                            entry = f"TCP:{dst}"

                            if entry not in dev["activity"]:
                                dev["activity"].append(entry)
                                dev["activity"] = dev["activity"][-10:]

        except Exception as e:
            log.error(f"Error paquete: {e}")

    # ─────────────────────────────────────────
    # CONSULTAS
    # ─────────────────────────────────────────

    def get_devices(self):
        return list(self._devices.values())