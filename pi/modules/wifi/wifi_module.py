from core.base_module import BaseModule
from modules.wifi.ids import WifiIDS
from modules.wifi.attacker import WifiAttacker
from modules.wifi.evil_twin import EvilTwin
from modules.wifi.pmkid import PMKIDCapture
from config import config

class WifiModule(BaseModule):
    def __init__(self):
        super().__init__('wifi')
        self.ids        = WifiIDS()
        self.attacker   = WifiAttacker()
        self.evil_twin  = EvilTwin()
        self.pmkid      = PMKIDCapture()

    def _setup(self) -> None:
        self.ids.start()
        self.logger.info(f"WiFi module listo en iface={config.WIFI_IFACE}")

    def _teardown(self) -> None:
        self.ids.stop()
        if self.evil_twin.is_running():
            self.evil_twin.stop()

    def get_status(self) -> dict:
        return {
            'module':     self.name,
            'status':     self.status.value,
            'iface':      config.WIFI_IFACE,
            'ids_active': self.ids._running,
            'evil_twin':  self.evil_twin.is_running(),
            'pmkid_busy': self.pmkid.is_running()
        }