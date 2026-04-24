class LocalDB:
    def __init__(self):
        pass

    # ── SESIONES ─────────────────────────────
    def create_session(self, session):
        pass

    def close_session(self, session_id, notes=""):
        pass

    def get_active_sessions(self) -> list:
        return []

    # ── ALERTS ───────────────────────────────
    def insert_alert(self, alert):
        pass

    def get_alerts(self, session_id=None, severity=None, acknowledged=None, limit=100, offset=0):
        return []

    def acknowledge_alert(self, alert_id):
        return True

    # ── EVENTS ───────────────────────────────
    def insert_event(self, event):
        return 1

    def get_events(self, session_id=None, module=None, limit=100, offset=0):
        return []

    # ── DEVICES ──────────────────────────────
    def upsert_device(self, device):
        pass

    def get_devices(self, session_id=None, device_type=None, limit=200, offset=0):
        return []

    # ── QUERY DIRECTA (para stats en rutas) ──
    def _execute(self, query, params=()):
        class Dummy:
            def fetchall(self): return []
            def fetchone(self): return None
        return Dummy()

    def close(self):
        pass


# 🔥 ESTO ES LO QUE TE FALTABA
db = LocalDB()