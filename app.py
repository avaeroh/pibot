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

# Camera capture function
def capture_frames():
    print("Starting video capture with OpenCV")

    # Try opening the camera
    cap = cv2.VideoCapture(0)
    # Check if the camera was opened successfully
    if not cap.isOpened():
        print("Error: Camera is not accessible.")
        sys.exit(1)  # Exit the application if camera cannot be opened

    print("Camera initialized successfully")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            time.sleep(1)  # Optional: Add a sleep time to avoid busy-waiting
            continue
        
        # Process and send the frame
        _, buffer = cv2.imencode('.jpg', frame)
        encoded_frame = base64.b64encode(buffer).decode('utf-8')
        socketio.emit('video_frame', {'data': encoded_frame})
        time.sleep(1 / 24)  # Simulate 24 fps

@socketio.on('connect')
def handle_connect():
    print("Client connected, starting video stream")
    thread = Thread(target=capture_frames)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
