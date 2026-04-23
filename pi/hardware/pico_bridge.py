"""STUB — Reemplazar con implementación real del Pico W bridge."""


class _FakePicoBridge:
    def is_connected(self) -> bool:
        return False

    def send(self, command: str, payload: dict = None) -> bool:
        return False


pico = _FakePicoBridge()
