# pi/api/routes/rfid.py
from flask import Blueprint, jsonify, request, current_app

rfid_bp = Blueprint("rfid", __name__)

def _mod():
    return current_app.config.get("MODULE_REGISTRY", {}).get("rfid")

@rfid_bp.get("/rfid/status")
def rfid_status():
    mod = _mod()
    if not mod: return jsonify({"error": "módulo no cargado"}), 404
    return jsonify(mod.info())

@rfid_bp.get("/rfid/whitelist")
def get_whitelist():
    mod = _mod()
    if not mod: return jsonify({"error": "módulo no cargado"}), 404
    return jsonify({"whitelist": mod.get_whitelist()})

@rfid_bp.post("/rfid/whitelist")
def add_whitelist():
    uid = (request.get_json(force=True) or {}).get("uid", "").upper()
    if not uid: return jsonify({"error": "uid requerido"}), 400
    mod = _mod()
    if not mod: return jsonify({"error": "módulo no cargado"}), 404
    ok = mod.add_to_whitelist(uid)
    return jsonify({"added": ok, "uid": uid})

@rfid_bp.delete("/rfid/whitelist/<uid>")
def remove_whitelist(uid: str):
    mod = _mod()
    if not mod: return jsonify({"error": "módulo no cargado"}), 404
    ok = mod.remove_from_whitelist(uid.upper())
    return jsonify({"removed": ok, "uid": uid.upper()})

@rfid_bp.post("/rfid/clone")
def clone_card():
    import asyncio
    mod = _mod()
    if not mod: return jsonify({"error": "módulo no cargado"}), 404
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(mod.clone_card())
    loop.close()
    return jsonify(result)

@rfid_bp.post("/rfid/verify")
def verify_card():
    uid = (request.get_json(force=True) or {}).get("uid", "").upper()
    if not uid: return jsonify({"error": "uid requerido"}), 400
    mod = _mod()
    if not mod: return jsonify({"error": "módulo no cargado"}), 404
    result = mod.cloner.verify(uid, timeout=10.0)
    return jsonify(result)
