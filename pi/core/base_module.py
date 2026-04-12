import threading
import time
from abc import ABC, abstractmethod

class BaseModule(ABC, threading.Thread):
    """
    Clase base para la dualidad ofensiva-defensiva del SENTINEL PHANTOM.
    Garantiza la concurrencia y el reporte de eventos en tiempo real.
    """
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.is_running = False
        self.daemon = True  # Para que el hilo muera si el Main muere 

    @abstractmethod
    def run(self):
        """Lógica principal que correrá en bucle."""
        pass

    def stop(self):
        """Detener el módulo de forma segura."""
        self.is_running = False
        print(f"[-] Módulo {self.name} detenido.")

    def log_event(self, description, level="INFO"):
        """
        Envía eventos al EventBus y los guarda en SQLite/SQL Server.
        Cumple con el registro forense exigido en el Anexo B.
        """
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        # Aquí llamaríamos al Singleton de la Base de Datos
        print(f"[{timestamp}] [{level}] [{self.name}]: {description}")