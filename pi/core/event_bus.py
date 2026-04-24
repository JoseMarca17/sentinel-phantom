import asyncio
from collections import defaultdict
from typing import Any, Callable
from database.local_db import insert_event, insert_alert # Asumiendo que existen estas funciones



bus.subscribe_all(global_persistence_handler)
from core.logger import get_logger

log = get_logger("core.event_bus")

Handler = Callable[[dict], Any]


class EventBus:
    """
    Bus de eventos singleton.
    Uso:
        bus = EventBus()
        bus.subscribe("wifi.alert", my_handler)
        await bus.publish("wifi.alert", {"ssid": "evil-ap"})
    """

    _instance: "EventBus | None" = None

    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)
        self._wildcard_subscribers: list[Handler] = []
        log.info("EventBus inicializado")

    # ── Suscripción ──────────────────────────────────────────────────────────

    def subscribe(self, topic: str, handler: Handler) -> None:
        """Suscribe un handler a un topic. Usa '*' para recibir todos los eventos."""
        if topic == "*":
            if handler not in self._wildcard_subscribers:
                self._wildcard_subscribers.append(handler)
                log.debug(f"Handler wildcard registrado: {handler.__qualname__}")
        else:
            if handler not in self._subscribers[topic]:
                self._subscribers[topic].append(handler)
                log.debug(f"Handler registrado en '{topic}': {handler.__qualname__}")

    def unsubscribe(self, topic: str, handler: Handler) -> None:
        """Elimina un handler de un topic."""
        if topic == "*":
            self._wildcard_subscribers = [h for h in self._wildcard_subscribers if h is not handler]
        elif topic in self._subscribers:
            self._subscribers[topic] = [h for h in self._subscribers[topic] if h is not handler]

    # ── Publicación async ────────────────────────────────────────────────────

    async def publish(self, topic: str, payload: dict | None = None) -> None:
        """Publica un evento de forma asíncrona a todos los handlers suscritos."""
        payload = payload or {}
        event = {"topic": topic, "payload": payload}

        handlers = self._subscribers.get(topic, []) + self._wildcard_subscribers

        if not handlers:
            log.debug(f"Evento sin handlers: {topic}")
            return

        log.debug(f"Publicando '{topic}' → {len(handlers)} handler(s)")

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:
                log.error(
                    f"Error en handler '{getattr(handler, '__qualname__', handler)}' "
                    f"para '{topic}': {exc}"
                )

    # ── Publicación síncrona ─────────────────────────────────────────────────

    def publish_sync(self, topic: str, payload: dict | None = None) -> None:
        """
        Publica un evento desde código síncrono (threads de hardware, callbacks, etc).

        Llama los handlers síncronos DIRECTAMENTE en el thread actual — sin pasar
        por el event loop — para evitar que los eventos queden en cola sin ejecutarse.

        Los handlers async se schedulan en el loop con run_coroutine_threadsafe.
        """
        payload = payload or {}
        event = {"topic": topic, "payload": payload}

        handlers = self._subscribers.get(topic, []) + self._wildcard_subscribers

        if not handlers:
            log.debug(f"Evento sin handlers: {topic}")
            return

        log.debug(f"publish_sync '{topic}' → {len(handlers)} handler(s)")

        for handler in handlers:
            try:
                result = handler(event)

                # Handler async — schedularlo en el loop si está corriendo
                if asyncio.iscoroutine(result):
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.run_coroutine_threadsafe(result, loop)
                        else:
                            loop.run_until_complete(result)
                    except RuntimeError:
                        asyncio.run(result)

            except Exception as exc:
                log.error(
                    f"Error en handler '{getattr(handler, '__qualname__', handler)}' "
                    f"para '{topic}': {exc}"
                )
    def global_persistence_handler(event_type, payload):
    # Guardar automáticamente todo lo que pase por el bus
    if "alert" in event_type:
        insert_alert(payload)
    elif "status" not in event_type: # No guardar status temporales
        insert_event(payload)

    # ── Utilidades ───────────────────────────────────────────────────────────

    def topics(self) -> list[str]:
        """Retorna todos los topics con al menos un suscriptor."""
        return list(self._subscribers.keys())

    def reset(self) -> None:
        """Limpia todos los suscriptores (útil en tests)."""
        self._subscribers.clear()
        self._wildcard_subscribers.clear()
        log.warning("EventBus reseteado — todos los handlers eliminados")


# Instancia global
bus = EventBus()