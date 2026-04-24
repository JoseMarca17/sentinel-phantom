import serial
import threading
import time

from core.logger import get_logger

log = get_logger("nrf")

# Tiempo de espera tras reset del ESP32 antes de mandar comandos
_BOOT_WAIT    = 2.5
# Timeout total para recibir SCAN_START después de mandar SCAN
_SCAN_TIMEOUT = 20


class NrfController:
    """
    Controla el ESP32 via Serial USB.

    Flujo WiFi Jam:
      1. scan()              → pide lista de redes al ESP32
      2. select(idx)         → elige la red de la lista
      3. start_wifi()        → manda WIFI:<nrfCh> y arranca el ataque

    Flujo BT Jam:
      1. start_bt()          → manda BT directamente
    """

    def __init__(self, port="/dev/ttyUSB1", baud=115200):
        self.port     = port
        self.baud     = baud
        self.ser      = None
        self.running  = False
        self._thread  = None

        self.networks     = []
        self.selected_idx = 0

        self._on_scan_done = None
        self._on_status    = None

    # ── CALLBACKS ─────────────────────────────────────────────────────────────

    def on_scan_done(self, fn):
        self._on_scan_done = fn

    def on_status(self, fn):
        self._on_status = fn

    # ── CONEXIÓN ──────────────────────────────────────────────────────────────

    def _connect(self) -> bool:
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(self.port, self.baud, timeout=2)
            # Vaciar buffer basura del boot
            time.sleep(_BOOT_WAIT)
            self.ser.reset_input_buffer()
            log.info(f"Serial conectado en {self.port}")
            return True
        except Exception as e:
            log.error(f"Error conectando Serial: {e}")
            return False

    def _send(self, cmd: str):
        if self.ser and self.ser.is_open:
            self.ser.write(f"{cmd}\n".encode())
            self.ser.flush()
            log.info(f"→ ESP32: {cmd}")

    def _notify(self, msg: str):
        log.info(f"[status] {msg}")
        if self._on_status:
            self._on_status(msg)

    def _readline(self, timeout: float = 3.0) -> str | None:
        """Lee una línea limpia. Devuelve None si hay timeout o error."""
        if not (self.ser and self.ser.is_open):
            return None
        self.ser.timeout = timeout
        try:
            raw  = self.ser.readline()
            line = raw.decode("utf-8", errors="ignore").strip()
            return line if line else None
        except Exception as e:
            log.warning(f"readline error: {e}")
            return None

    def _drain_until(self, keyword: str, timeout: float = 5.0) -> bool:
        """
        Lee líneas descartando las que no interesan hasta encontrar keyword
        o agotar timeout.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = deadline - time.time()
            line = self._readline(timeout=min(remaining, 1.0))
            if line is None:
                continue
            log.info(f"[ESP32] {line}")
            if keyword in line:
                return True
        return False

    # ── ESCANEO ───────────────────────────────────────────────────────────────

    def scan(self):
        t = threading.Thread(target=self._scan_thread, daemon=True)
        t.start()

    def _scan_thread(self):
        if not self._connect():
            self._notify("ESP32 no encontrado")
            return

        self.networks = []
        self._notify("Escaneando...")

        # Mandar SCAN y esperar SCAN_START (el ESP32 puede tardar ~3s en escanear)
        self._send("SCAN")

        log.info("Esperando SCAN_START...")
        if not self._drain_until("SCAN_START", timeout=_SCAN_TIMEOUT):
            log.error("Timeout esperando SCAN_START")
            self._notify("Sin respuesta ESP32")
            self._close()
            return

        # Leer redes hasta SCAN_END
        log.info("Leyendo redes...")
        deadline = time.time() + 30
        while time.time() < deadline:
            line = self._readline(timeout=5.0)
            if line is None:
                continue

            log.info(f"[ESP32] {line}")

            if line.startswith("SCAN_END:"):
                total = int(line.split(":")[1])
                log.info(f"Escaneo terminado: {total} redes encontradas")
                break

            if line.startswith("NETWORK:"):
                # NETWORK:<idx>:<ssid>:<wifi_ch>:<rssi>
                parts = line.split(":", 4)
                if len(parts) == 5:
                    _, idx, ssid, ch, rssi = parts
                    try:
                        self.networks.append({
                            "idx":    int(idx),
                            "ssid":   ssid,
                            "ch":     int(ch),
                            "rssi":   int(rssi),
                            "nrf_ch": self._wifi_ch_to_nrf(int(ch)),
                        })
                    except ValueError:
                        log.warning(f"Línea mal formada: {line}")

        self._close()

        log.info(f"Redes parseadas: {len(self.networks)}")
        if self._on_scan_done:
            self._on_scan_done(self.networks)

    # ── SELECCIÓN ─────────────────────────────────────────────────────────────

    def select(self, idx: int):
        if 0 <= idx < len(self.networks):
            self.selected_idx = idx
            net = self.networks[idx]
            log.info(f"Red seleccionada: {net['ssid']} ch{net['ch']} (nRF ch{net['nrf_ch']})")
        else:
            log.warning(f"Índice {idx} fuera de rango ({len(self.networks)} redes)")

    # ── ATAQUES ───────────────────────────────────────────────────────────────

    def start_wifi(self):
        if not self.networks:
            self._notify("Sin redes. Escanea primero")
            return
        net = self.networks[self.selected_idx]
        self._launch("WIFI", net)

    def start_bt(self):
        self._launch("BT", None)

    def _launch(self, mode: str, net):
        # Detener ataque previo si existe
        if self._thread and self._thread.is_alive():
            self.stop()
            self._thread.join(timeout=3)

        self.running = True
        self._thread = threading.Thread(
            target=self._attack_thread,
            args=(mode, net),
            daemon=True
        )
        self._thread.start()

    def _attack_thread(self, mode: str, net):
        if not self._connect():
            self._notify("ESP32 no encontrado")
            return

        try:
            if mode == "WIFI":
                cmd   = f"WIFI:{net['nrf_ch']}"
                label = f"Jam: {net['ssid'][:14]}"
            else:
                cmd   = "BT"
                label = "BT Jam ACTIVO"

            self._send(cmd)

            # Esperar READY
            if self._drain_until("READY", timeout=6):
                self._notify(label)
            else:
                self._notify("Sin respuesta ESP32")
                return

            # Leer logs del ESP32 mientras el ataque está activo
            while self.running:
                line = self._readline(timeout=1.0)
                if line:
                    log.info(f"[ESP32] {line}")

        except Exception as e:
            log.error(f"Error en ataque: {e}")
            self._notify(f"Error: {str(e)[:15]}")

        finally:
            self._close()

    # ── STOP ──────────────────────────────────────────────────────────────────

    def stop(self):
        self.running = False
        try:
            if self.ser and self.ser.is_open:
                self._send("STOP")
                time.sleep(0.3)
            else:
                # Reconectar solo para mandar STOP
                s = serial.Serial(self.port, self.baud, timeout=2)
                time.sleep(0.5)
                s.write(b"STOP\n")
                s.flush()
                s.close()
        except Exception as e:
            log.warning(f"Error al detener: {e}")
        finally:
            self._close()

    def _close(self):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass

    # ── UTILIDADES ────────────────────────────────────────────────────────────

    @staticmethod
    def _wifi_ch_to_nrf(wifi_ch: int) -> int:
        freqs = [0,
                 2412, 2417, 2422, 2427, 2432, 2437,
                 2442, 2447, 2452, 2457, 2462, 2467,
                 2472, 2484]
        if wifi_ch < 1 or wifi_ch > 14:
            return 37
        return freqs[wifi_ch] - 2400