import os
from pathlib import Path

from flask import Flask
from flask_socketio import SocketIO

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR))
socketio = SocketIO(app, cors_allowed_origins="*")


def get_app_mode():
    return os.getenv("PIBOT_MODE", "control").lower()


@app.route("/")
def index():
    page = "independent-mode.html" if get_app_mode() == "independent" else "control-mode.html"
    return app.send_static_file(page)


@app.route("/control")
def control_page():
    return app.send_static_file("control-mode.html")


@app.route("/independent")
def independent_page():
    return app.send_static_file("independent-mode.html")
