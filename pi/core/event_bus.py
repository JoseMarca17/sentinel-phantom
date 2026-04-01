# pi/core/event_bus.py
import threading
import logging
from typing import Callable, Dict, List, Any

logger = logging.getLogger(__name__)

class EventBus:
    """
    Sistema pub/sub simple para comunicación entre módulos.
    
    Uso:
        bus = EventBus.get_instance()
        
        # Suscribirse a un evento
        bus.subscribe("wifi.deauth_detected", mi_funcion)
        
        # Publicar un evento
        bus.publish("wifi.deauth_detected", {"mac": "AA:BB:CC", "severity": "critical"})
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        """Singleton — todos los módulos usan la misma instancia"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def subscribe(self, event: str, callback: Callable):
        """Registrar una función para escuchar un evento"""
        with self._lock:
            if event not in self._subscribers:
                self._subscribers[event] = []
            self._subscribers[event].append(callback)
            logger.debug(f"Suscripcion: {callback.__name__} → {event}")

    def unsubscribe(self, event: str, callback: Callable):
        """Cancelar suscripción"""
        with self._lock:
            if event in self._subscribers:
                self._subscribers[event].remove(callback)

    def publish(self, event: str, data: Dict[str, Any] = {}):
        """
        Publicar un evento — notifica a todos los suscriptores.
        Cada callback corre en su propio hilo para no bloquear.
        """
        with self._lock:
            callbacks = self._subscribers.get(event, []).copy()

        if not callbacks:
            logger.debug(f"Evento sin suscriptores: {event}")
            return

        for callback in callbacks:
            t = threading.Thread(
                target=self._call_safe,
                args=(callback, event, data),
                daemon=True
            )
            t.start()

    def _call_safe(self, callback: Callable, event: str, data: Dict):
        """Llama al callback capturando cualquier excepción"""
        try:
            callback(event, data)
        except Exception as e:
            logger.error(f"Error en callback {callback.__name__} para {event}: {e}")

# Eventos del sistema — referencia
EVENTS = {
    # WiFi
    "wifi.deauth_detected":   "Deauth frame detectado",
    "wifi.beacon_flood":      "Beacon flood detectado",
    "wifi.evil_twin":         "Evil Twin detectado",
    "wifi.new_ap":            "Nuevo AP encontrado",
    "wifi.probe_request":     "Probe request capturado",

    # Bluetooth
    "bt.device_found":        "Dispositivo BT detectado",
    "bt.unknown_device":      "Dispositivo BT no autorizado",
    "bt.device_lost":         "Dispositivo BT desapareció",

    # RFID
    "rfid.card_read":         "Tarjeta RFID leída",
    "rfid.card_cloned":       "Tarjeta RFID clonada",

    # TSCM
    "tscm.device_found":      "Dispositivo oculto detectado",

    # nRF24
    "nrf24.drone_detected":   "Drone detectado",
    "nrf24.signal_found":     "Señal Nordic detectada",

    # Sistema
    "system.module_started":  "Módulo iniciado",
    "system.module_stopped":  "Módulo detenido",
    "system.error":           "Error del sistema",
}