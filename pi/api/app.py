from flask import Flask, render_template  # Añade render_template
from flask_socketio import SocketIO
from core.event_bus import event_bus
from config import SERVER_HOST, SERVER_PORT

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

def handle_sentinel_events(event_type, data):
    socketio.emit('new_event', {'type': event_type, 'payload': data})

event_bus.subscribe(handle_sentinel_events)

@app.route('/')
def index():
    return render_template('index.html') # Esto sirve el dashboard

def start_api():
    socketio.run(app, host=SERVER_HOST, port=SERVER_PORT, debug=False, use_reloader=False)