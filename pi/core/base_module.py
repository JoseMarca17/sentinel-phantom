# """
# SENTINEL PHANTOM - Módulo Base
# Clase abstracta que deben heredar todos los módulos tácticos.
# Gestiona ciclo de vida: init → start → stop, y publica eventos al bus.
# """

# import asyncio
# import time
# from abc import ABC, abstractmethod
# from enum import Enum
# from typing import Any

# from core.event_bus import bus
# from core.logger import get_logger


# class ModuleStatus(str, Enum):
#     STOPPED   = "STOPPED"
#     STARTING  = "STARTING"
#     RUNNING   = "RUNNING"
#     STOPPING  = "STOPPING"
#     ERROR     = "ERROR"
#     DISABLED  = "DISABLED"


# class BaseModule(ABC):
#     """
#     Clase base para módulos tácticos de Sentinel Phantom.

#     Cada módulo debe implementar:
#         - _setup()   → inicialización de hardware/recursos
#         - _run()     → loop principal (corrutina)
#         - _teardown() → limpieza al detener

#     Publica automáticamente eventos:
#         - module.<name>.started
#         - module.<name>.stopped
#         - module.<name>.error
#     """

#     def __init__(self, name: str, enabled: bool = True) -> None:
#         self.name    = name
#         self.enabled = enabled
#         self.status  = ModuleStatus.DISABLED if not enabled else ModuleStatus.STOPPED
#         self.log     = get_logger(f"module.{name}")
#         self._task: asyncio.Task | None = None
#         self._stop_event = asyncio.Event()
#         self._started_at: float | None = None
#         self._error_count: int = 0

#     # ── Ciclo de vida ────────────────────────────────────────────────────────

#     async def start(self) -> None:
#         if not self.enabled:
#             self.log.warning(f"Módulo '{self.name}' deshabilitado — ignorando start()")
#             return
#         if self.status == ModuleStatus.RUNNING:
#             self.log.warning(f"Módulo '{self.name}' ya está corriendo")
#             return

#         self.log.info(f"Iniciando módulo '{self.name}'...")
#         self.status = ModuleStatus.STARTING
#         self._stop_event.clear()

#         try:
#             await self._setup()
#             self.status = ModuleStatus.RUNNING
#             self._started_at = time.time()
#             self._task = asyncio.create_task(self._safe_run(), name=f"module.{self.name}")
#             await bus.publish(f"module.{self.name}.started", {"module": self.name})
#             self.log.info(f"Módulo '{self.name}' RUNNING ✓")
#         except Exception as exc:
#             self.status = ModuleStatus.ERROR
#             self._error_count += 1
#             self.log.error(f"Error al iniciar '{self.name}': {exc}")
#             await bus.publish(f"module.{self.name}.error", {"module": self.name, "error": str(exc)})
#             raise

#     async def stop(self) -> None:
#         if self.status not in (ModuleStatus.RUNNING, ModuleStatus.STARTING):
#             return

#         self.log.info(f"Deteniendo módulo '{self.name}'...")
#         self.status = ModuleStatus.STOPPING
#         self._stop_event.set()

#         if self._task and not self._task.done():
#             self._task.cancel()
#             try:
#                 await self._task
#             except asyncio.CancelledError:
#                 pass

#         try:
#             await self._teardown()
#         except Exception as exc:
#             self.log.error(f"Error en teardown de '{self.name}': {exc}")

#         self.status = ModuleStatus.STOPPED
#         await bus.publish(f"module.{self.name}.stopped", {"module": self.name})
#         self.log.info(f"Módulo '{self.name}' STOPPED")

#     async def _safe_run(self) -> None:
#         """Envuelve _run() capturando excepciones y actualizando estado."""
#         try:
#             await self._run()
#         except asyncio.CancelledError:
#             pass
#         except Exception as exc:
#             self._error_count += 1
#             self.status = ModuleStatus.ERROR
#             self.log.error(f"Error fatal en módulo '{self.name}': {exc}", exc_info=True)
#             await bus.publish(f"module.{self.name}.error", {"module": self.name, "error": str(exc)})

#     # ── Abstracciones ────────────────────────────────────────────────────────

#     @abstractmethod
#     async def _setup(self) -> None:
#         """Inicialización de hardware/recursos. Se llama antes de _run()."""

#     @abstractmethod
#     async def _run(self) -> None:
#         """Loop principal del módulo. Debe respetar _stop_event para terminar limpiamente."""

#     @abstractmethod
#     async def _teardown(self) -> None:
#         """Limpieza de recursos al detener."""

#     # ── Helpers ──────────────────────────────────────────────────────────────

#     async def emit(self, event_type: str, payload: dict) -> None:
#         """Publica un evento con prefijo del módulo."""
#         topic = f"{self.name}.{event_type}"
#         payload.setdefault("module", self.name)
#         await bus.publish(topic, payload)

#     def emit_sync(self, event_type: str, payload: dict) -> None:
#         """Versión síncrona de emit() para usar desde threads."""
#         topic = f"{self.name}.{event_type}"
#         payload.setdefault("module", self.name)
#         bus.publish_sync(topic, payload)

#     @property
#     def uptime(self) -> float | None:
#         """Segundos desde que el módulo inició. None si no está corriendo."""
#         if self._started_at and self.status == ModuleStatus.RUNNING:
#             return time.time() - self._started_at
#         return None

#     def info(self) -> dict[str, Any]:
#         """Retorna estado resumido del módulo para la API."""
#         return {
#             "name":        self.name,
#             "status":      self.status.value,
#             "enabled":     self.enabled,
#             "uptime":      round(self.uptime, 1) if self.uptime is not None else None,
#             "error_count": self._error_count,
#         }

#     def __repr__(self) -> str:
#         return f"<{self.__class__.__name__} name={self.name!r} status={self.status.value}>"

import asyncio
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from core.event_bus import bus
from core.logger import get_logger


class ModuleStatus(str, Enum):
    STOPPED   = "STOPPED"
    STARTING  = "STARTING"
    RUNNING   = "RUNNING"
    STOPPING  = "STOPPING"
    ERROR     = "ERROR"
    DISABLED  = "DISABLED"


class BaseModule(ABC):

    def __init__(self, name: str, enabled: bool = True) -> None:
        self.name    = name
        self.enabled = enabled
        self.status  = ModuleStatus.DISABLED if not enabled else ModuleStatus.STOPPED
        self.log     = get_logger(f"module.{name}")
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._started_at: float | None = None
        self._error_count: int = 0

    async def start(self) -> None:
        if not self.enabled:
            return

        if self.status == ModuleStatus.RUNNING:
            return

        self.status = ModuleStatus.STARTING
        self._stop_event.clear()

        try:
            await self._setup()
            self.status = ModuleStatus.RUNNING
            self._started_at = time.time()

            self._task = asyncio.create_task(self._safe_run())

            await bus.publish(f"module.{self.name}.started", {"module": self.name})

        except Exception as exc:
            self.status = ModuleStatus.ERROR
            self._error_count += 1
            await bus.publish(f"module.{self.name}.error", {"error": str(exc)})

    async def stop(self) -> None:
        if self.status != ModuleStatus.RUNNING:
            return

        self.status = ModuleStatus.STOPPING
        self._stop_event.set()

        if self._task:
            self._task.cancel()

        try:
            await self._teardown()
        except:
            pass

        self.status = ModuleStatus.STOPPED
        await bus.publish(f"module.{self.name}.stopped", {"module": self.name})

    async def _safe_run(self):
        try:
            await self._run()
        except Exception as e:
            self.status = ModuleStatus.ERROR
            self._error_count += 1
            await bus.publish(f"module.{self.name}.error", {"error": str(e)})

    # 🔥 puente sync → async
    def start_sync(self):
        asyncio.create_task(self.start())

    def stop_sync(self):
        asyncio.create_task(self.stop())

    @abstractmethod
    async def _setup(self): pass

    @abstractmethod
    async def _run(self): pass

    @abstractmethod
    async def _teardown(self): pass

    async def emit(self, event_type: str, payload: dict):
        await bus.publish(f"{self.name}.{event_type}", payload)

    def emit_sync(self, event_type: str, payload: dict):
        bus.publish_sync(f"{self.name}.{event_type}", payload)

    def info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "error_count": self._error_count,
        }