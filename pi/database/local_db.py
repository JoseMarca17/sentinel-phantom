"""STUB — Reemplazar cuando se implemente SQLite."""


class _FakeDB:
    def create_session(self, session): pass
    def insert_alert(self, alert): pass
    def insert_event(self, event): pass
    def close_session(self, session_id, notes=""): pass
    def upsert_device(self, device): pass
    def get_active_sessions(self) -> list: return []
    def close(self): pass


db = _FakeDB()
