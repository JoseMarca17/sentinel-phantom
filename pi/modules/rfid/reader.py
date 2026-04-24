"""
SENTINEL PHANTOM - RFID Reader
Lee PN532 (I2C, 13.56 MHz) y RC522 (SPI, 125 kHz) via ESP32 por USB serial.
"""

import json
import time
import serial
from typing import Optional

from config import ESP32_PORT, ESP32_BAUD
from core.logger import get_logger

log = get_logger("module.rfid.reader")


class RFIDReader:
    """
    Lee tarjetas RFID/NFC desde el ESP32 via USB serial.
    El ESP32 maneja PN532 y RC522 y devuelve JSON.
    """

    def __init__(self):
        self._ser: Optional[serial.Serial] = None
        self._last_uid = ""
        self._cooldown = 2.0
        self._last_time = 0.0
        self._connect()

    def _connect(self):
        try:
            self._ser = serial.Serial(
                port=ESP32_PORT,
                baudrate=ESP32_BAUD,
                timeout=1.0,
            )
            time.sleep(2)
            self._ser.reset_input_buffer()
            self._ser.write(b"PING\n")
            resp = self._ser.readline().decode("utf-8", errors="ignore").strip()
            if "PONG" in resp:
                log.info(f"ESP32 conectado en {ESP32_PORT}")
            else:
                log.warning(f"ESP32 no respondió PING (resp: {resp!r})")
        except serial.SerialException as exc:
            log.error(f"No se pudo abrir {ESP32_PORT}: {exc}")
            self._ser = None

    @property
    def connected(self) -> bool:
        return self._ser is not None and self._ser.is_open

    def read_once(self) -> Optional[dict]:
        """
        Intenta leer una tarjeta. Retorna dict con uid/source/type o None.
        Bloqueante hasta timeout (1s por defecto del serial).
        """
        if not self.connected:
            self._connect()
            return None

        try:
            line = self._ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                return None

            data = json.loads(line)

            if data.get("event") != "SCAN":
                return None

            uid = data.get("uid", "")
            if not uid:
                return None

            now = time.time()
            if uid == self._last_uid and (now - self._last_time) < self._cooldown:
                return None

            self._last_uid = uid
            self._last_time = now

            return {
                "uid":        uid,
                "source":     data.get("source", "UNKNOWN"),
                "type":       self._detect_type(data.get("source", "")),
                "authorized": data.get("authorized", False),
                "raw":        data,
            }

        except json.JSONDecodeError:
            pass
        except serial.SerialException as exc:
            log.error(f"Error serial: {exc}")
            self._ser = None
        return None

    def _detect_type(self, source: str) -> str:
        if source == "PN532":
            return "MIFARE/NFC (13.56 MHz)"
        if source == "RC522":
            return "RFID (125 kHz)"
        return "UNKNOWN"

    def send_command(self, cmd: str, timeout: float = 3.0) -> Optional[dict]:
        """
        Envía un comando al ESP32 y espera su respuesta JSON.
        Ignora eventos SCAN que lleguen mientras espera — esos son del
        loop de escaneo normal del ESP32 y no son la respuesta al comando.
        """
        if not self.connected:
            return None
        try:
            self._ser.reset_input_buffer()
            self._ser.write(f"{cmd}\n".encode())

            deadline = time.time() + timeout
            while time.time() < deadline:
                line = self._ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # Ignorar SCANs que el ESP32 emita mientras procesa el comando
                    if data.get("event") == "SCAN":
                        log.debug(f"SCAN ignorado mientras esperaba respuesta a {cmd!r}")
                        continue
                    # Cualquier otra respuesta es nuestra
                    return data
                except json.JSONDecodeError:
                    continue  # línea de debug del ESP32

            log.warning(f"Timeout esperando respuesta para comando: {cmd!r}")
            return None

        except Exception as exc:
            log.error(f"Error enviando comando {cmd!r}: {exc}")
            return None

    def ping(self) -> bool:
        r = self.send_command("PING")
        return r is not None and r.get("event") == "PONG"

    def get_status(self) -> Optional[dict]:
        return self.send_command("STATUS")

    def close(self):
        if self._ser and self._ser.is_open:
            self._ser.close()