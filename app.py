from flask import Flask, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from utility.movement_controls import Forwards, Backwards, Left, Right, Stop
import os
import time
from threading import Thread
import io
import base64

try:
    from picamera2 import Picamera2, Preview
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/forwards', methods=['POST'])
def move_forwards():
    Forwards()
    return jsonify({"message": "Moving forwards"})

@app.route('/backwards', methods=['POST'])
def move_backwards():
    Backwards()
    return jsonify({"message": "Moving backwards"})

@app.route('/left', methods=['POST'])
def move_left():
    Left()
    return jsonify({"message": "Turning left"})

@app.route('/right', methods=['POST'])
def move_right():
    Right()
    return jsonify({"message": "Turning right"})

@app.route('/stop', methods=['POST'])
def stop_movement():
    Stop()
    return jsonify({"message": "Stopped"})

def capture_frames():
    if CAMERA_AVAILABLE:
        camera = Picamera2()
        camera.resolution = (640, 480)
        camera.framerate = 24
        time.sleep(2)  # Camera warm-up time
        stream = io.BytesIO()
        for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
            stream.seek(0)
            frame = stream.read()
            encoded_frame = base64.b64encode(frame).decode('utf-8')
            socketio.emit('video_frame', {'data': encoded_frame})
            stream.seek(0)
            stream.truncate()
    else:
        # Mock camera functionality for development on non-Raspberry Pi systems
        import cv2
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            _, buffer = cv2.imencode('.jpg', frame)
            encoded_frame = base64.b64encode(buffer).decode('utf-8')
            socketio.emit('video_frame', {'data': encoded_frame})
            time.sleep(1 / 24)  # Simulate 24 fps

@socketio.on('connect')
def handle_connect():
    thread = Thread(target=capture_frames)
    thread.start()

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)