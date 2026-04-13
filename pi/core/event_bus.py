import asyncio
from collections import defaultdict
from typing import Any, Callable, Coroutine

from core.logger import get_logger

log = get_logger("core.event_bus")


# Tipo para handlers (pueden ser sync o async)
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
        self._wildcard_subscribers: list[Handler] = []   # suscritos a "*"
        self._loop: asyncio.AbstractEventLoop | None = None
        log.info("EventBus inicializado")

    # ── Suscripción ──────────────────────────────────────────────────────────

    def subscribe(self, topic: str, handler: Handler) -> None:
        """Suscribe un handler a un topic.  Usa '*' para recibir todos los eventos."""
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

    # ── Publicación ──────────────────────────────────────────────────────────

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
                log.error(f"Error en handler '{getattr(handler, '__qualname__', handler)}' para '{topic}': {exc}")

    def publish_sync(self, topic: str, payload: dict | None = None) -> None:
        """
        Publica un evento desde código síncrono (ej. threads de hardware).
        Usa el loop existente si está corriendo, de lo contrario asyncio.run().
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.publish(topic, payload), loop)
            else:
                loop.run_until_complete(self.publish(topic, payload))
        except RuntimeError:
            asyncio.run(self.publish(topic, payload))

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