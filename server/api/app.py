"""
SENTINEL PHANTOM — Servidor Central Flask
Corre en la laptop del equipo.
Recibe sincronizaciones desde la Pi y sirve reportes al Dashboard.
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from database.db import close_thread_connection, test_connection, execute, executemany, fetchall, fetchone
from api.routes.reports import reports_bp
from api.routes.history import history_bp
from api.routes.export  import export_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "phantom-server-2026")

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Blueprints ─────────────────────────────────────────────────────────────
    prefix = "/api"
    app.register_blueprint(reports_bp, url_prefix=prefix)
    app.register_blueprint(history_bp, url_prefix=prefix)
    app.register_blueprint(export_bp,  url_prefix=prefix)

    # ── Health ─────────────────────────────────────────────────────────────────
    @app.get("/api/health")
    def health():
        db_ok = test_connection()
        return jsonify({
            "status":   "ok" if db_ok else "degraded",
            "db":       "connected" if db_ok else "error",
            "server":   "SENTINEL PHANTOM — Servidor Central",
        }), 200 if db_ok else 503

    # ── Endpoints de sincronización (recibe datos de la Pi) ────────────────────

    def _api_key_ok() -> bool:
        expected = os.getenv("SERVER_API_KEY", "")
        if not expected:
            return True  # sin clave configurada → aceptar todo (dev)
        return request.headers.get("X-API-Key") == expected

    @app.before_request
    def check_api_key():
        if request.path.startswith("/api/sync"):
            if not _api_key_ok():
                return jsonify({"error": "Unauthorized"}), 401

    @app.post("/sync/sessions")
    def sync_sessions():
        records = (request.get_json(force=True) or {}).get("records", [])
        if not records:
            return jsonify({"synced": 0})
        sql = """
            MERGE sessions AS target
            USING (VALUES (?,?,?,?,?)) AS src(id,device_id,started_at,ended_at,notes)
            ON target.id = src.id
            WHEN NOT MATCHED THEN
                INSERT (id,device_id,started_at,ended_at,notes)
                VALUES (src.id,src.device_id,src.started_at,src.ended_at,src.notes);
        """
        data = [(r["id"],r["device_id"],r["started_at"],r.get("ended_at"),r.get("notes")) for r in records]
        executemany(sql, data)
        return jsonify({"synced": len(records)})

    @app.post("/sync/events")
    def sync_events():
        records = (request.get_json(force=True) or {}).get("records", [])
        if not records:
            return jsonify({"synced": 0})
        sql = """
            IF NOT EXISTS (SELECT 1 FROM events WHERE id=? AND session_id=?)
                INSERT INTO events (id,session_id,timestamp,module,event_type,payload)
                VALUES (?,?,?,?,?,?)
        """
        data = [
            (r["id"], r["session_id"],
             r["id"], r["session_id"], r["timestamp"], r["module"], r["event_type"], r.get("payload"))
            for r in records
        ]
        executemany(sql, data)
        return jsonify({"synced": len(records)})

    @app.post("/sync/alerts")
    def sync_alerts():
        records = (request.get_json(force=True) or {}).get("records", [])
        if not records:
            return jsonify({"synced": 0})
        sql = """
            IF NOT EXISTS (SELECT 1 FROM alerts WHERE id=? AND session_id=?)
                INSERT INTO alerts
                    (id,session_id,timestamp,module,alert_type,severity,description,device_mac,extra,acknowledged)
                VALUES (?,?,?,?,?,?,?,?,?,?)
        """
        data = [
            (r["id"], r["session_id"],
             r["id"], r["session_id"], r["timestamp"], r["module"],
             r["alert_type"], r["severity"], r["description"],
             r.get("device_mac"), r.get("extra"), r.get("acknowledged", 0))
            for r in records
        ]
        executemany(sql, data)
        return jsonify({"synced": len(records)})

    @app.post("/sync/devices")
    def sync_devices():
        records = (request.get_json(force=True) or {}).get("records", [])
        if not records:
            return jsonify({"synced": 0})
        sql = """
            MERGE devices AS target
            USING (VALUES (?,?,?,?,?,?,?,?,?,?,?)) AS src
                (id,session_id,first_seen,last_seen,device_type,mac,vendor,ssid,signal_dbm,extra,threat_level)
            ON target.id = src.id
            WHEN MATCHED THEN
                UPDATE SET last_seen=src.last_seen, signal_dbm=src.signal_dbm,
                           extra=src.extra, threat_level=src.threat_level
            WHEN NOT MATCHED THEN
                INSERT (id,session_id,first_seen,last_seen,device_type,mac,vendor,ssid,signal_dbm,extra,threat_level)
                VALUES (src.id,src.session_id,src.first_seen,src.last_seen,src.device_type,
                        src.mac,src.vendor,src.ssid,src.signal_dbm,src.extra,src.threat_level);
        """
        data = [
            (r["id"],r.get("session_id"),r["first_seen"],r["last_seen"],r["device_type"],
             r.get("mac"),r.get("vendor"),r.get("ssid"),r.get("signal_dbm"),
             r.get("extra"),r.get("threat_level","INFO"))
            for r in records
        ]
        executemany(sql, data)
        return jsonify({"synced": len(records)})

    # ── Cleanup de conexión por request ────────────────────────────────────────
    @app.teardown_appcontext
    def teardown(_exc):
        close_thread_connection()

    # ── Error handlers ─────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint no encontrado"}), 404

    @app.errorhandler(500)
    def internal(e):
        return jsonify({"error": "Error interno del servidor"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8000))
    debug = os.getenv("SERVER_DEBUG", "false").lower() == "true"
    print(f"[PHANTOM SERVER] Iniciando en http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)