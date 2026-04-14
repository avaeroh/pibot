# pibot

My robot Pi! This has been built with:

- Raspberry Pi 4B  
- CamJam EduKit #3 (motor controller + GPIO)  
- 10,000mAh power bank (for Pi)  
- 4x AA batteries (for motors)  
- PiCamera (note: IR version has not worked reliably)

![The Bot](references/pibot.png)

---

## Current Functionality

- Flask-based webserver for PiCamera streaming and real-time WASD/button control  
- Lower-latency MJPEG video streaming using `libcamera-vid` and a direct HTTP feed
- Graceful teardown of camera processes and cleanup on exit  
- Automatic install/run via Makefile
- Can be developed against without GPIO functionality (utilising a mocked import of GPIO)
- Hold-to-move control flow over Socket.IO with explicit stop on key release, disconnect, or browser blur
- Readable `pytest` suite covering movement controls, routes/logging, Socket.IO control events, and camera lifecycle/stream parsing behaviour

---

## Requirements

- Raspberry Pi OS (Bookworm recommended)  
- Raspberry Pi 4B  
- PiCamera v2+  
- Python 3.11+  
- `make` cli binary
- Network access to the Pi from a browser

---

## Setup & Usage

### 1. (Optional) Create a `.env` file for local configuration

```env
PYTHONUNBUFFERED=1
FLASK_PORT=5000
LIBCAM_FPS=10
LIBCAM_QUALITY=85
LIBCAM_ROTATION=180 # Depending on which way up your camera is
MOCK_GPIO=true # If you are developing on a PI with a GPIO and you don't want to move the motors while debugging
```

The app loads `.env` automatically on startup.

---

### 2. Install dependencies

```bash
make all
```

Installs system tools, Python packages, and prepares folders.

If you are developing off-device, the Python dependencies are still enough to run the test suite locally. Pi-specific hardware access is mocked in tests.

---

### 3. Run the test suite

```bash
make test
```

This will:

- Run the `pytest` suite from the local virtual environment
- Force `MOCK_GPIO=true` so motor controls can be exercised safely off-device
- Validate the Flask routes, log buffer, movement helpers, and mocked camera stream lifecycle

---

### 4. Run the pibot webserver

```bash
make run
```

This will:

- Start `libcamera-vid` in the background
- Stream frames through a named pipe (`/tmp/vidstream.mjpeg`)
- Serve the control interface via Flask + Socket.IO
- Expose the camera at `/video_feed` as an MJPEG stream
- Expose logs via `/logs` for debugging

### 5. Open the control page from another device

Find the Pi's LAN IP on the Pi:

```bash
hostname -I
```

Then, from a phone or computer on the same network, open:

```text
http://<your-pi-ip>:5000
```

Examples:

- `http://192.168.1.42:5000`
- `http://raspberrypi.local:5000` if mDNS is working on your network

Useful routes:

- `/` - main control page served from `static/index.html`
- `/video_feed` - raw MJPEG camera stream
- `/logs` - recent server logs for debugging

### 6. Drive the robot

Once the page is open:

- Hold `W`, `A`, `S`, or `D` to keep the robot moving
- Release the key to stop
- Press `Space` to force an immediate stop
- Or use the on-screen buttons with click-and-hold / touch-and-hold
- If the browser loses focus or disconnects, the robot is told to stop as a safety fallback

---

### 7. (Optional) Download TensorFlow Lite models

```bash
make download-models
```

Places `.tflite` files in the `models/` folder.

---

### 8. Clean up (including FIFO and models)

```bash
make clean
```

---

## Developer Notes

- Video is streamed over HTTP as MJPEG via `/video_feed`, which avoids the previous OpenCV re-encode and base64 WebSocket path
- The camera feed is managed using `libcamera-vid`, started on demand and cleaned up by the Flask server
- Movement control is stateful rather than time-based: the browser sends `move_start` and `stop` Socket.IO events instead of repeated timed movement requests
- The server binds to `0.0.0.0` and uses `FLASK_PORT` if set, otherwise port `5000`
- Tests are organised by responsibility:
  - `tests/test_01_movement_controls.py`
  - `tests/test_02_routes_and_logging.py`
  - `tests/test_03_camera_stream.py`
- Tests are designed to run away from the Raspberry Pi by mocking GPIO access and camera/process interactions
- Logs are stored in a ring buffer and accessible at:

```
http://<your-pi-ip>:5000/logs
```

- If the video feed fails, the browser will automatically display the last 50 server logs
- A `Thread` is used to stream frames from OpenCV
- The named pipe (`/tmp/vidstream.mjpeg`) is created and destroyed automatically

---

## Troubleshooting

If the video feed does not appear:

1. Check the browser console and the `#output` log box
2. Visit `/logs` directly in your browser to see server logs
3. Confirm the FIFO exists and isn't blocked:

```bash
ls -l /tmp/vidstream.mjpeg
```

4. Ensure no stale `libcamera-vid` processes are running:

```bash
ps aux | grep libcamera-vid
```

If stuck, run:

```bash
make kill-camera
make run
```

---

## TODO

- Improve frontend with camera status indicator & quality
- add object detection & non-user driven behaviour
