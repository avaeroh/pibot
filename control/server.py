from control.app_instance import app, socketio
import signal
import atexit
from utility.logger import setup_logging, log
from control import movement_routes
from camera.stream import start_streaming, cleanup_camera
import utility.movement_controls

setup_logging(app)

def handle_exit(sig, frame):
    log(f"Received signal {sig}, exiting.")
    cleanup_camera()
    exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)
atexit.register(cleanup_camera)

@socketio.on('connect')
def handle_connect():
    log("Client connected, starting video stream")
    start_streaming(socketio)
