from pathlib import Path

from flask import Flask
from flask_socketio import SocketIO

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR))
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route("/")
def index():
    return app.send_static_file("index.html")
