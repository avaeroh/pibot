from control.app_instance import app, socketio
from flask import Response, jsonify
import signal
import atexit
from utility.logger import setup_logging, log
from control import movement_routes
from camera.stream import generate_mjpeg_stream, cleanup_camera
from independent.service import independent_mode_service
from utility.movement_controls import Forwards, Backwards, Left, Right, Stop

setup_logging(app)

def handle_exit(sig, frame):
    log(f"Received signal {sig}, exiting.")
    cleanup_camera()
    independent_mode_service.cleanup()
    exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)
atexit.register(cleanup_camera)
atexit.register(independent_mode_service.cleanup)

@socketio.on('connect')
def handle_connect():
    log("Client connected")


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


@app.route('/video_feed')
def video_feed():
    return Response(
        generate_mjpeg_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
    )


@app.route('/independent/video_feed')
def independent_video_feed():
    return Response(
        independent_mode_service.stream_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
    )


@app.route('/independent/logs')
def independent_logs():
    return jsonify(independent_mode_service.get_log_entries())
