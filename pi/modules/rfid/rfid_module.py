"""
SENTINEL PHANTOM - Módulo RFID/NFC
Ofensivo: lectura UID, dump MIFARE, clonado
Defensivo: whitelist, detección de clones, alertas, log forense
"""

import asyncio
import json
import uuid
from datetime import datetime

from core.base_module import BaseModule
from core.logger import get_logger
from database.local_db import db
from database.models import Alert, Device, Event
from config import DEVICE_ID

from modules.rfid.reader  import RFIDReader
from modules.rfid.cloner  import RFIDCloner
from modules.rfid.defense import RFIDDefense

log = get_logger("module.rfid")


class RFIDModule(BaseModule):

    def __init__(self):
        super().__init__("rfid", enabled=True)
        self.reader  = None
        self.cloner  = None
        self.defense = None
        self._session_id = None
        self._scan_count  = 0
        self._alert_count = 0

    async def _setup(self):
        self.reader  = RFIDReader()
        self.cloner  = RFIDCloner(self.reader)
        self.defense = RFIDDefense()
        # Obtener sesión activa
        sessions = db.get_active_sessions()
        self._session_id = sessions[0]["id"] if sessions else str(uuid.uuid4())
        log.info(f"RFID module listo — sesión {self._session_id[:8]}")

    async def _run(self):
        log.info("RFID escaneando — acerca una tarjeta...")
        while not self._stop_event.is_set():
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.reader.read_once
                )
                if result:
                    await self._process_scan(result)
            except Exception as exc:
                log.error(f"Error en ciclo RFID: {exc}")
            await asyncio.sleep(0.1)

    async def _teardown(self):
        log.info(f"RFID detenido — {self._scan_count} scans, {self._alert_count} alertas")

    # ── Procesamiento de cada scan ────────────────────────────────────────────

    async def _process_scan(self, result: dict):
        self._scan_count += 1
        uid      = result["uid"]
        source   = result["source"]   # PN532 | RC522
        card_type = result.get("type", "UNKNOWN")

        log.info(f"[{source}] UID detectado: {uid} ({card_type})")

        # 1. Verificación de Integridad (Código Secreto en Bloque 4)
        # Solo intentamos leer si la fuente es el PN532 (NFC/MIFARE)
        block_data = ""
        if source == "PN532":
            log.info(f"Verificando firma digital para {uid}...")
            # Llamamos al comando READ 4 definido en tu ESP32
            resp = await asyncio.get_event_loop().run_in_executor(
                None, self.reader.send_command, "READ 4"
            )
            if resp and resp.get("event") == "READ_OK":
                block_data = resp.get("content", "")

        # 2. Análisis defensivo (Duplicidad física + Firma secreta)
        # Pasamos block_data a analyze() para detectar clones
        threats = self.defense.analyze(uid, source, block_data)

        # 3. Guardar dispositivo en DB
        self._save_device(uid, source, card_type)

        # 4. Guardar evento
        self._save_event("card_detected", {
            "uid": uid, "source": source, "type": card_type, "threats": threats
        })

        # 5. Disparar alertas si el motor de defensa encontró algo
        for threat in threats:
            await self._raise_alert(uid, threat)

        # 6. Publicar en el bus (Dashboard en tiempo real)
        # Una tarjeta es autorizada SOLAMENTE si está en whitelist Y no tiene amenazas
        is_auth = self.defense.is_authorized(uid) and len(threats) == 0

        await self.emit("card_detected", {
            "uid":        uid,
            "source":     source,
            "type":       card_type,
            "authorized": is_auth,
            "threats":    threats,
            "session_id": self._session_id,
        })

    # ── Alerta ────────────────────────────────────────────────────────────────

    async def _raise_alert(self, uid: str, threat: dict):
        self._alert_count += 1
        alert = Alert(
            session_id  = self._session_id,
            module      = "rfid",
            alert_type  = threat["type"],
            severity    = threat["severity"],
            description = threat["description"],
            device_mac  = uid,
        )
        db.insert_alert(alert)
        await self.emit("alert", {
            "uid":         uid,
            "alert_type":  threat["type"],
            "severity":    threat["severity"],
            "description": threat["description"],
            "session_id":  self._session_id,
        })
        log.warning(f"[ALERTA {threat['severity']}] {threat['description']}")

    # ── Helpers DB ────────────────────────────────────────────────────────────

    def _save_device(self, uid: str, source: str, card_type: str):
        now = datetime.utcnow().isoformat()
        device = Device(
            id          = f"rfid-{uid}",
            session_id  = self._session_id,
            first_seen  = now,
            last_seen   = now,
            device_type = "rfid",
            mac         = uid,
            vendor      = source,
            extra       = json.dumps({"card_type": card_type}),
            threat_level= "INFO" if self.defense.is_authorized(uid) else "MEDIUM",
        )
        db.upsert_device(device)

    def _save_event(self, event_type: str, payload: dict):
        event = Event(
            session_id = self._session_id,
            module     = "rfid",
            event_type = event_type,
            payload    = json.dumps(payload),
        )
        db.insert_event(event)

    # ── API pública para comandos externos ────────────────────────────────────

    async def clone_card(self) -> dict:
        """Clona la tarjeta presente en el lector."""
        log.info("Iniciando clonado...")
        result = await asyncio.get_event_loop().run_in_executor(
            None, self.cloner.clone
        )
        self._save_event("clone_attempt", result)
        return result

    def add_to_whitelist(self, uid: str) -> bool:
        ok = self.defense.add_authorized(uid)
        self._save_event("whitelist_add", {"uid": uid})
        log.info(f"UID {uid} agregado a whitelist")
        return ok

    def remove_from_whitelist(self, uid: str) -> bool:
        ok = self.defense.remove_authorized(uid)
        self._save_event("whitelist_remove", {"uid": uid})
        return ok

    def get_whitelist(self) -> list:
        return self.defense.get_whitelist()

    def info(self) -> dict:
        base = super().info()
        base.update({
            "scan_count":  self._scan_count,
            "alert_count": self._alert_count,
            "whitelist":   self.defense.get_whitelist() if self.defense else [],
        })
        return base
