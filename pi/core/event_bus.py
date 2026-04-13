from collections import defaultdict
from typing import Callable, Any
from core.logger import get_logger

logger = get_logger('event_bus')

class EventBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers: dict[str, list[Callable]] = defaultdict(list)
        return cls._instance

    def subscribe(self, event: str, callback: Callable) -> None:
        self._subscribers[event].append(callback)
        logger.debug(f"Subscribed '{callback.__qualname__}' to event '{event}'")

    def unsubscribe(self, event: str, callback: Callable) -> None:
        self._subscribers[event] = [
            cb for cb in self._subscribers[event] if cb != callback
        ]

    def publish(self, event: str, data: Any = None) -> None:
        listeners = self._subscribers.get(event, [])
        logger.debug(f"Publishing '{event}' → {len(listeners)} listener(s)")
        for callback in listeners:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error en listener '{callback.__qualname__}' para '{event}': {e}")

# Instancia global (singleton)
event_bus = EventBus()