import sys
from flask import Flask, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from utility.movement_controls import Forwards, Backwards, Left, Right, Stop
import os
import time
from threading import Thread
import io
import base64
import cv2

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="*")

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
    print("Starting video capture with OpenCV")

    # Try opening the video stream with a generic backend
    cap = cv2.VideoCapture(0, cv2.CAP_ANY)
    time.sleep(1)  # Allow time for the camera to initialize

    if not cap.isOpened():
        print("Error: Camera is not accessible.")
        sys.exit(1)

    print("Camera initialized successfully")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            time.sleep(10)
            continue

        # Debugging: Confirm frame capture and size
        print("Frame captured successfully, sending via WebSocket...")

        _, buffer = cv2.imencode('.jpg', frame)
        encoded_frame = base64.b64encode(buffer).decode('utf-8')

        # Send the frame via socket.io
        socketio.emit('video_frame', {'data': encoded_frame}, namespace='/')

        time.sleep(1 / 24)  # 24 FPS

@socketio.on('connect')
def handle_connect():
    print("Client connected, starting video stream")
    thread = Thread(target=capture_frames)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)