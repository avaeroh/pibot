from control.app_instance import app, socketio
import signal
import atexit
from utility.logger import setup_logging, log
from control import movement_routes
from camera.stream import start_streaming, cleanup_camera
from utility.movement_controls import Forwards, Backwards, Left, Right, Stop

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


@socketio.on('move_start')
def handle_move_start(data):
    direction = (data or {}).get('direction')
    handlers = {
        'forwards': Forwards,
        'backwards': Backwards,
        'left': Left,
        'right': Right,
    }

    handler = handlers.get(direction)
    if handler is None:
        log(f"Ignoring unknown movement direction: {direction}")
        return {'status': 'error', 'message': 'Unknown direction'}

    handler()
    log(f"Movement started: {direction}")
    return {'status': 'ok', 'message': f'Moving {direction}'}


@socketio.on('stop')
def handle_stop():
    Stop()
    log("Movement stopped")
    return {'status': 'ok', 'message': 'Stopped'}


@socketio.on('disconnect')
def handle_disconnect():
    log("Client disconnected, stopping movement")
    Stop()
