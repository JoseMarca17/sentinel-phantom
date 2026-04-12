import queue

class EventBus:
    """Sistema Pub/Sub para comunicación inter-modular."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance.subscribers = []
        return cls._instance

    def publish(self, event_type, data):
        """Publica un evento a todos los módulos interesados."""
        for callback in self.subscribers:
            callback(event_type, data)

    def subscribe(self, callback):
        """Registra un nuevo suscriptor."""
        self.subscribers.append(callback)

event_bus = EventBus()