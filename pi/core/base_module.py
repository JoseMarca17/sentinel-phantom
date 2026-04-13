from abc import ABC, abstractmethod
from enum import Enum
from core.logger import get_logger
from core.event_bus import event_bus

class ModuleStatus(Enum):
    STOPPED  = "stopped"
    STARTING = "starting"
    RUNNING  = "running"
    ERROR    = "error"

class BaseModule(ABC):
    def __init__(self, name: str):
        self.name   = name
        self.status = ModuleStatus.STOPPED
        self.logger = get_logger(name)
        self.bus    = event_bus

    # ── Ciclo de vida ──────────────────────────────────────────
    def start(self) -> bool:
        self.logger.info(f"[{self.name}] Iniciando...")
        self.status = ModuleStatus.STARTING
        try:
            self._setup()
            self.status = ModuleStatus.RUNNING
            self.bus.publish('module.started', {'module': self.name})
            self.logger.info(f"[{self.name}] Corriendo.")
            return True
        except Exception as e:
            self.status = ModuleStatus.ERROR
            self.logger.error(f"[{self.name}] Fallo al iniciar: {e}")
            self.bus.publish('module.error', {'module': self.name, 'error': str(e)})
            return False

    def stop(self) -> None:
        self.logger.info(f"[{self.name}] Deteniendo...")
        try:
            self._teardown()
        except Exception as e:
            self.logger.warning(f"[{self.name}] Error al detener: {e}")
        finally:
            self.status = ModuleStatus.STOPPED
            self.bus.publish('module.stopped', {'module': self.name})

    # ── Métodos abstractos que cada módulo DEBE implementar ────
    @abstractmethod
    def _setup(self) -> None:
        """Inicialización de hardware y recursos del módulo."""

    @abstractmethod
    def _teardown(self) -> None:
        """Liberación de recursos al detener."""

    @abstractmethod
    def get_status(self) -> dict:
        """Retorna el estado actual del módulo como dict (para la API)."""

    # ── Helpers ────────────────────────────────────────────────
    def emit(self, event: str, data: dict = None) -> None:
        """Shortcut para publicar eventos con prefijo del módulo."""
        self.bus.publish(f'{self.name}.{event}', data or {})

    def is_running(self) -> bool:
        return self.status == ModuleStatus.RUNNING

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} status={self.status.value}>"