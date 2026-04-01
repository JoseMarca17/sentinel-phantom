# pi/modules/base_module.py
import threading
import logging
from abc import ABC, abstractmethod
from core.event_bus import EventBus
from core.config import config

class BaseModule(ABC):
    """
    Clase base que todos los módulos heredan.
    
    Para crear un módulo nuevo:
        class MiModulo(BaseModule):
            def start(self): ...
            def stop(self):  ...
            def status(self): ...
    """

    def __init__(self, name: str):
        self.name = name
        self.running = False
        self.bus = EventBus.get_instance()
        self.logger = logging.getLogger(f"module.{name}")
        self._thread = None

    @abstractmethod
    def start(self):
        """Arrancar el módulo"""
        pass

    @abstractmethod
    def stop(self):
        """Detener el módulo limpiamente"""
        pass

    @abstractmethod
    def status(self) -> dict:
        """Retornar estado actual del módulo"""
        pass

    def _run_in_thread(self, target, *args):
        """Correr una función en hilo separado"""
        self._thread = threading.Thread(
            target=target,
            args=args,
            daemon=True,
            name=f"module-{self.name}"
        )
        self._thread.start()

    def publish(self, event: str, data: dict):
        """Publicar evento al bus"""
        self.bus.publish(event, data)