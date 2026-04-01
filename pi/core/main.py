# pi/core/main.py
import logging
import signal
import sys
import time
from core.config import config
from core.event_bus import EventBus
from core.logger import CentinelLogger

logger = logging.getLogger(__name__)

class CentinelPhantom:
    """Orquestador principal del sistema"""

    def __init__(self):
        self.bus = EventBus.get_instance()
        self.db_logger = CentinelLogger()
        self.modules = {}
        self.running = False

    def _load_modules(self):
        """Carga solo los módulos habilitados en .env"""

        if config.MODULES_ENABLED.get("wifi"):
            from modules.wifi.wifi_module import WiFiModule
            self.modules["wifi"] = WiFiModule()
            logger.info("Modulo WiFi cargado")

        if config.MODULES_ENABLED.get("bluetooth"):
            from modules.bluetooth.bt_module import BluetoothModule
            self.modules["bluetooth"] = BluetoothModule()
            logger.info("Modulo Bluetooth cargado")

        if config.MODULES_ENABLED.get("tscm"):
            from modules.tscm.tscm_module import TSCMModule
            self.modules["tscm"] = TSCMModule()
            logger.info("Modulo TSCM cargado")

        if config.MODULES_ENABLED.get("rfid"):
            from modules.rfid.rfid_module import RFIDModule
            self.modules["rfid"] = RFIDModule()
            logger.info("Modulo RFID cargado")

        if config.MODULES_ENABLED.get("nrf24"):
            from modules.nrf24.nrf24_module import NRF24Module
            self.modules["nrf24"] = NRF24Module()
            logger.info("Modulo nRF24 cargado")

    def start(self):
        """Arrancar el sistema completo"""
        logger.info("="*50)
        logger.info("  CENTINEL PHANTOM — Iniciando sistema")
        logger.info("="*50)

        self._load_modules()

        # Arrancar cada módulo en su propio hilo
        for name, module in self.modules.items():
            try:
                module.start()
                self.bus.publish("system.module_started", {
                    "module": name,
                    "severity": "info"
                })
            except Exception as e:
                logger.error(f"Error arrancando modulo {name}: {e}")

        self.running = True
        logger.info(f"Sistema activo con {len(self.modules)} modulos")

        # Mantener el proceso vivo
        while self.running:
            time.sleep(1)

    def stop(self):
        """Apagar el sistema limpiamente"""
        logger.info("Apagando Centinel Phantom...")
        self.running = False

        for name, module in self.modules.items():
            try:
                module.stop()
                logger.info(f"Modulo {name} detenido")
            except Exception as e:
                logger.error(f"Error deteniendo modulo {name}: {e}")

        logger.info("Sistema apagado correctamente")


def main():
    system = CentinelPhantom()

    # Manejar Ctrl+C y señales del sistema
    def signal_handler(sig, frame):
        system.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    system.start()


if __name__ == "__main__":
    main()#Hola
# pi/core/main.py
import logging
import signal
import sys
import time
from core.config import config
from core.event_bus import EventBus
from core.logger import CentinelLogger

logger = logging.getLogger(__name__)

class CentinelPhantom:
    """Orquestador principal del sistema"""

    def __init__(self):
        self.bus = EventBus.get_instance()
        self.db_logger = CentinelLogger()
        self.modules = {}
        self.running = False

    def _load_modules(self):
        """Carga solo los módulos habilitados en .env"""

        if config.MODULES_ENABLED.get("wifi"):
            from modules.wifi.wifi_module import WiFiModule
            self.modules["wifi"] = WiFiModule()
            logger.info("Modulo WiFi cargado")

        if config.MODULES_ENABLED.get("bluetooth"):
            from modules.bluetooth.bt_module import BluetoothModule
            self.modules["bluetooth"] = BluetoothModule()
            logger.info("Modulo Bluetooth cargado")

        if config.MODULES_ENABLED.get("tscm"):
            from modules.tscm.tscm_module import TSCMModule
            self.modules["tscm"] = TSCMModule()
            logger.info("Modulo TSCM cargado")

        if config.MODULES_ENABLED.get("rfid"):
            from modules.rfid.rfid_module import RFIDModule
            self.modules["rfid"] = RFIDModule()
            logger.info("Modulo RFID cargado")

        if config.MODULES_ENABLED.get("nrf24"):
            from modules.nrf24.nrf24_module import NRF24Module
            self.modules["nrf24"] = NRF24Module()
            logger.info("Modulo nRF24 cargado")

    def start(self):
        """Arrancar el sistema completo"""
        logger.info("="*50)
        logger.info("  CENTINEL PHANTOM — Iniciando sistema")
        logger.info("="*50)

        self._load_modules()

        # Arrancar cada módulo en su propio hilo
        for name, module in self.modules.items():
            try:
                module.start()
                self.bus.publish("system.module_started", {
                    "module": name,
                    "severity": "info"
                })
            except Exception as e:
                logger.error(f"Error arrancando modulo {name}: {e}")

        self.running = True
        logger.info(f"Sistema activo con {len(self.modules)} modulos")

        # Mantener el proceso vivo
        while self.running:
            time.sleep(1)

    def stop(self):
        """Apagar el sistema limpiamente"""
        logger.info("Apagando Centinel Phantom...")
        self.running = False

        for name, module in self.modules.items():
            try:
                module.stop()
                logger.info(f"Modulo {name} detenido")
            except Exception as e:
                logger.error(f"Error deteniendo modulo {name}: {e}")

        logger.info("Sistema apagado correctamente")


def main():
    system = CentinelPhantom()

    # Manejar Ctrl+C y señales del sistema
    def signal_handler(sig, frame):
        system.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    system.start()


if __name__ == "__main__":
    main()