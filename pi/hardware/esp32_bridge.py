"""STUB — Reemplazar con implementación real del ESP32 bridge."""


class _FakeESP32Bridge:
    def is_connected(self) -> bool:
        return False

    def send(self, command: str, payload: dict = None) -> bool:
        return False


esp32 = _FakeESP32Bridge()
