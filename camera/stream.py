import os
import subprocess
from shutil import which

from utility.logger import log

FIFO_PATH = "/tmp/vidstream.mjpeg"
VIDEO_PROCESS = None
JPEG_START = b"\xff\xd8"
JPEG_END = b"\xff\xd9"

WIDTH = int(os.getenv("LIBCAM_WIDTH", 640))
HEIGHT = int(os.getenv("LIBCAM_HEIGHT", 480))
FPS = int(os.getenv("LIBCAM_FPS", 10))
QUALITY = int(os.getenv("LIBCAM_QUALITY", 85))
ROTATION = int(os.getenv("LIBCAM_ROTATION", 180))


def get_camera_command():
    for command in ("rpicam-vid", "libcamera-vid"):
        if which(command):
            return command

    raise FileNotFoundError(
        "No supported camera command found. Install rpicam-vid or libcamera-vid."
    )


def cleanup_camera():
    global VIDEO_PROCESS
    log("Cleaning up camera...")
    if VIDEO_PROCESS and VIDEO_PROCESS.poll() is None:
        log("Terminating camera process")
        VIDEO_PROCESS.terminate()
        VIDEO_PROCESS.wait()
    VIDEO_PROCESS = None
    if os.path.exists(FIFO_PATH):
        log(f"Removing FIFO at {FIFO_PATH}")
        os.remove(FIFO_PATH)


def start_libcamera_stream():
    global VIDEO_PROCESS
    if VIDEO_PROCESS and VIDEO_PROCESS.poll() is None:
        return

    if not os.path.exists(FIFO_PATH):
        log(f"Creating FIFO at {FIFO_PATH}")
        os.mkfifo(FIFO_PATH)

    camera_command = get_camera_command()
    log(f"Starting {camera_command} at {WIDTH}x{HEIGHT}, {FPS}fps, quality {QUALITY}")
    VIDEO_PROCESS = subprocess.Popen(
        [
            camera_command,
            "-t",
            "0",
            "--codec",
            "mjpeg",
            "--inline",
            "--width",
            str(WIDTH),
            "--height",
            str(HEIGHT),
            "--framerate",
            str(FPS),
            "--quality",
            str(QUALITY),
            "--rotation",
            str(ROTATION),
            "-o",
            FIFO_PATH,
        ]
    )


def iter_mjpeg_frames(stream, chunk_size=4096):
    buffer = b""
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break

        buffer += chunk

        while True:
            start_index = buffer.find(JPEG_START)
            if start_index == -1:
                buffer = b""
                break

            end_index = buffer.find(JPEG_END, start_index + len(JPEG_START))
            if end_index == -1:
                buffer = buffer[start_index:]
                break

            frame = buffer[start_index : end_index + len(JPEG_END)]
            yield frame
            buffer = buffer[end_index + len(JPEG_END) :]


def generate_mjpeg_stream():
    start_libcamera_stream()
    log("Streaming MJPEG frames directly from FIFO")
    with open(FIFO_PATH, "rb") as fifo_stream:
        for frame in iter_mjpeg_frames(fifo_stream):
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame
                + b"\r\n"
            )
