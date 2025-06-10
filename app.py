import sys
import os
import time
import io
import base64
import cv2
import atexit
import signal
import subprocess
import datetime
from threading import Thread
from flask import Flask, jsonify, send_from_directory, request
from flask_socketio import SocketIO, emit
from utility.movement_controls import Forwards, Backwards, Left, Right, Stop
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="*")

FIFO_PATH = "/tmp/vidstream.mjpeg"
VIDEO_PROCESS = None
log_buffer = []

# Read camera settings from env with defaults
WIDTH = int(os.getenv("LIBCAM_WIDTH", 640))
HEIGHT = int(os.getenv("LIBCAM_HEIGHT", 480))
FPS = int(os.getenv("LIBCAM_FPS", 10))
QUALITY = int(os.getenv("LIBCAM_QUALITY", 85))
ROTATION = int(os.getenv("LIBCAM_ROTATION", 180))

def log(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    log_buffer.append(line)
    if len(log_buffer) > 50:
        log_buffer.pop(0)

@app.route('/logs')
def get_logs():
    return jsonify(log_buffer)

def cleanup():
    global VIDEO_PROCESS
    log("Cleaning up...")

    if VIDEO_PROCESS and VIDEO_PROCESS.poll() is None:
        log("Terminating libcamera-vid process")
        VIDEO_PROCESS.terminate()
        VIDEO_PROCESS.wait()

    if os.path.exists(FIFO_PATH):
        log(f"Removing FIFO at {FIFO_PATH}")
        os.remove(FIFO_PATH)

atexit.register(cleanup)

def signal_handler(sig, frame):
    log(f"Received signal {sig}, exiting.")
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

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

def start_libcamera_stream():
    global VIDEO_PROCESS

    if not os.path.exists(FIFO_PATH):
        log(f"Creating FIFO at {FIFO_PATH}")
        os.mkfifo(FIFO_PATH)

    log(f"Starting libcamera-vid at {WIDTH}x{HEIGHT}, {FPS} fps, quality {QUALITY}")
    VIDEO_PROCESS = subprocess.Popen([
        "libcamera-vid",
        "-t", "0",
        "--inline",
        "--width", str(WIDTH),
        "--height", str(HEIGHT),
        "--framerate", str(FPS),
        "--quality", str(QUALITY),
        "--rotation", str(ROTATION),
        "-o", FIFO_PATH
    ])

def capture_frames():
    log("Opening FIFO stream with OpenCV")
    cap = cv2.VideoCapture(FIFO_PATH)

    if not cap.isOpened():
        log("Error: Failed to open video stream from pipe.")
        return

    log("Video stream opened successfully")

    while True:
        
        ret, frame = cap.read()
        if not ret:
            log("Failed to read frame from stream")
            time.sleep(1)
            continue

        _, buffer = cv2.imencode('.jpg', frame)
        encoded_frame = base64.b64encode(buffer).decode('utf-8')

        socketio.emit('video_frame', {'data': encoded_frame}, namespace='/')
        time.sleep(1 / FPS)

@socketio.on('connect')
def handle_connect():
    log("Client connected, starting video stream")
    start_libcamera_stream()
    thread = Thread(target=capture_frames)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
