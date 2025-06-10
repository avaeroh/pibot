import os
import subprocess
import time
import cv2
import base64
from threading import Thread
from utility.logger import log

FIFO_PATH = "/tmp/vidstream.mjpeg"
VIDEO_PROCESS = None

WIDTH = int(os.getenv("LIBCAM_WIDTH", 640))
HEIGHT = int(os.getenv("LIBCAM_HEIGHT", 480))
FPS = int(os.getenv("LIBCAM_FPS", 10))
QUALITY = int(os.getenv("LIBCAM_QUALITY", 85))
ROTATION = int(os.getenv("LIBCAM_ROTATION", 180))

def cleanup_camera():
    global VIDEO_PROCESS
    log("Cleaning up camera...")
    if VIDEO_PROCESS and VIDEO_PROCESS.poll() is None:
        log("Terminating libcamera-vid process")
        VIDEO_PROCESS.terminate()
        VIDEO_PROCESS.wait()
    if os.path.exists(FIFO_PATH):
        log(f"Removing FIFO at {FIFO_PATH}")
        os.remove(FIFO_PATH)

def start_libcamera_stream():
    global VIDEO_PROCESS
    if not os.path.exists(FIFO_PATH):
        log(f"Creating FIFO at {FIFO_PATH}")
        os.mkfifo(FIFO_PATH)
    log(f"Starting libcamera-vid at {WIDTH}x{HEIGHT}, {FPS}fps, quality {QUALITY}")
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

def capture_frames(socketio):
    log("Opening FIFO stream with OpenCV")
    cap = cv2.VideoCapture(FIFO_PATH)
    if not cap.isOpened():
        log("Error: Failed to open video stream from pipe.")
        return
    log("Video stream opened successfully")
    while True:
        for _ in range(2): cap.grab()  # skip stale frames
        ret, frame = cap.read()
        if not ret:
            log("Failed to read frame from stream")
            time.sleep(0.1)
            continue
        _, buffer = cv2.imencode('.jpg', frame)
        encoded_frame = base64.b64encode(buffer).decode('utf-8')
        socketio.emit('video_frame', {'data': encoded_frame}, namespace='/')
        time.sleep(1 / FPS)

def start_streaming(socketio):
    start_libcamera_stream()
    thread = Thread(target=capture_frames, args=(socketio,))
    thread.daemon = True
    thread.start()
