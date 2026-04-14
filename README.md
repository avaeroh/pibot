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

- Two browser-accessible run modes: `control` and `independent`
- Flask-based webserver for PiCamera streaming and real-time WASD/button control  
- Lower-latency MJPEG video streaming using Raspberry Pi camera apps and a direct HTTP feed
- Graceful teardown of camera processes and cleanup on exit  
- Automatic install/run via Makefile targets for each mode
- Can be developed against without GPIO functionality (utilising a mocked import of GPIO)
- Hold-to-move control flow over Socket.IO with explicit stop on key release, disconnect, or browser blur
- Independent mode powered by TensorFlow Lite object detection buckets for `people` and `cat`
- Independent mode behaviour hooks:
  - `cat` -> 360 spin
  - `people` -> wiggle routine
- Readable `pytest` suite covering movement controls, routes/logging, mode routing, Socket.IO control events, camera lifecycle/stream parsing, and independent-mode detection logic

---

## Requirements

- Raspberry Pi OS (Bookworm recommended)  
- Raspberry Pi 4B  
- PiCamera v2+  
- Python 3.11+  
- `make` cli binary
- Network access to the Pi from a browser

Independent mode note:

- `control` mode uses the normal project environment
- `independent` mode uses a separate Python 3.9 environment on Raspberry Pi Linux `aarch64` because of upstream `tflite-support` wheel availability

---

## Setup & Usage

### 1. (Optional) Create a `.env` file for local configuration

```env
PYTHONUNBUFFERED=1
FLASK_PORT=5000
PIBOT_MODE=control
LIBCAM_FPS=10
LIBCAM_QUALITY=85
LIBCAM_ROTATION=180 # Depending on which way up your camera is
MOCK_GPIO=true # If you are developing on a PI with a GPIO and you don't want to move the motors while debugging
TFLITE_MODEL=models/efficientdet_lite0.tflite
INDEPENDENT_FPS=6
INDEPENDENT_QUALITY=70
TFLITE_DETECTION_INTERVAL=0.4
SPIN_360_SECONDS=0.95
WIGGLE_TURN_SECONDS=0.12
WIGGLE_MOVE_SECONDS=0.15
```

The app loads `.env` automatically on startup.

---

### 2. Install dependencies

```bash
make all
```

Installs system tools, prepares folders, creates both virtual environments, installs the control-mode dependencies into `.venv-control`, and installs the independent-mode stack into `.venv-independent`.

If you are developing off-device, the Python dependencies are still enough to run the test suite locally. Pi-specific hardware access is mocked in tests.

Split environment summary:

- `.venv-control` -> control mode and tests
- `.venv-independent` -> independent mode and TensorFlow Lite

You can also install them separately:

```bash
make install-control
make install-independent
make bootstrap-independent
```

Independent-mode prerequisites on Raspberry Pi OS Bookworm:

1. Install the normal system packages first:

```bash
make install-deps
```

2. Use the opt-in bootstrap target:

```bash
make bootstrap-independent
```

This will:

- install the Linux build prerequisites for Python 3.9
- install `pyenv` into `~/.pyenv` if it is missing
- build Python `3.9.19`
- install the independent-mode environment into `.venv-independent`

3. Confirm that the independent environment is now on Python 3.9:

```bash
.venv-independent/bin/python --version
```

4. If you already have your own Python 3.9 interpreter and do not want the bootstrap path, you can still install directly:

```bash
make install-independent
```

If your Python 3.9 binary lives somewhere non-standard, point Make at it explicitly:

```bash
make install-independent PYTHON39=/path/to/python3.9
```

---

### 3. Run the test suite

```bash
make test
```

This will:

- Run the `pytest` suite from `.venv-control`
- Force `MOCK_GPIO=true` so motor controls can be exercised safely off-device
- Validate the Flask routes, mode routing, log buffers, movement helpers, camera stream lifecycle, and independent-mode bucket logic

---

### 4. (Optional) Download TensorFlow Lite models

```bash
make download-models
```

Places `.tflite` files in the `models/` folder.

This is required for `independent` mode unless you provide your own model path via `TFLITE_MODEL`.

---

### 5. Run the pibot webserver

The default `run` target respects `PIBOT_MODE` from your environment or `.env`.

```bash
make run
```

You can also start a mode explicitly:

```bash
make run-control
make run-independent
```

This will:

- Start `rpicam-vid` on Bookworm, or fall back to `libcamera-vid` on older setups
- Serve the mode-specific interface from `/`
- Expose logs via `/logs` for debugging
- Expose the active camera feed as MJPEG over HTTP

Runtime environments:

- `make run` and `make run-control` use `.venv-control`
- `make run-independent` uses `.venv-independent`

Mode summary:

- `control` mode:
  - root page `/` serves the manual control UI
  - video feed is served at `/video_feed`
  - movement is driven by browser input over Socket.IO
- `independent` mode:
  - root page `/` serves the TFLite monitoring UI
  - annotated detection feed is served at `/independent/video_feed`
  - browser log is available at `/independent/logs`
  - detections are bucketed into `people` and `cat`
  - `cat` triggers a 360 spin
  - `people` triggers a wiggle routine

### 6. Open the pibot page from another device

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

- `/` - page for the currently selected mode
- `/control` - manual control page
- `/independent` - TFLite independent-mode page
- `/video_feed` - raw control-mode camera stream
- `/independent/video_feed` - annotated independent-mode feed
- `/independent/logs` - independent-mode detection and behaviour log
- `/logs` - recent server logs for debugging

### 7. Use control mode

Open `/control`, or run the app with `PIBOT_MODE=control` and open `/`.

- Hold `W`, `A`, `S`, or `D` to keep the robot moving
- Release the key to stop
- Press `Space` to force an immediate stop
- Or use the on-screen buttons with click-and-hold / touch-and-hold
- If the browser loses focus or disconnects, the robot is told to stop as a safety fallback

---

### 8. Use independent mode

Open `/independent`, or run the app with `PIBOT_MODE=independent` and open `/`.

- The camera feed is annotated in the browser with TFLite detections
- A browser log shows matches and triggered behaviours
- `people` currently means any detected `person`
- `cat` currently means any detected `cat`
- Detections are throttled with `TFLITE_DETECTION_INTERVAL` and a lower default FPS to stay friendlier to a Raspberry Pi 4
- Behaviour execution is cooldown-limited so repeated detections do not spam motion commands

---

### 9. Clean up (including FIFO and models)

```bash
make clean
```

---

## Developer Notes

- Video is streamed over HTTP as MJPEG via `/video_feed`, which avoids the previous OpenCV re-encode and base64 WebSocket path
- The camera feed is managed using `rpicam-vid` on Bookworm, falling back to `libcamera-vid` when available on older systems
- Movement control is stateful rather than time-based: the browser sends `move_start` and `stop` Socket.IO events instead of repeated timed movement requests
- Independent mode uses a throttled TensorFlow Lite detection loop and keeps the annotated JPEG feed in memory for browser clients
- Independent mode currently depends on `tflite-support==0.4.4`, which is why it runs from the separate Python 3.9 `.venv-independent` environment on Raspberry Pi `aarch64`
- The current independent-mode buckets are intentionally lightweight:
  - `people` -> any `person` detection
  - `cat` -> any `cat` detection
- The current behaviours are best-effort time-based motor routines, not encoder-verified precise motion
- The server binds to `0.0.0.0` and uses `FLASK_PORT` if set, otherwise port `5000`
- Static pages are organised by mode:
  - `static/control-mode.html`
  - `static/independent-mode.html`
- Tests are organised by mode:
  - `tests/control/test_control_mode.py`
  - `tests/control/test_control_stream.py`
  - `tests/independent/test_independent_mode.py`
- Tests are designed to run away from the Raspberry Pi by mocking GPIO access, camera/process interactions, and TFLite-dependent pieces
- Logs are stored in a ring buffer and accessible at:

```
http://<your-pi-ip>:5000/logs
```

- If the independent-mode feed fails, the browser log will surface the detection-service errors from `/independent/logs`
- Control mode uses a FIFO-backed camera stream; independent mode uses a background detection worker and an annotated MJPEG stream

---

## Troubleshooting

If the video feed does not appear:

1. Check the browser console and the `#output` log box
2. Visit `/logs` directly in your browser to see server logs
3. Confirm the FIFO exists and isn't blocked:

```bash
ls -l /tmp/vidstream.mjpeg
```

4. Ensure no stale camera processes are running:

```bash
ps aux | grep -E 'rpicam-vid|libcamera-vid'
```

If independent mode does not start:

1. Confirm the model exists:

```bash
ls -l models/efficientdet_lite0.tflite
```

2. Confirm the TFLite dependencies are installed:

```bash
.venv-independent/bin/pip show tflite-support
```

3. Check the Python version in your virtual environment:

```bash
.venv-independent/bin/python --version
```

Independent mode currently expects Python 3.9 there.

4. If `python3.9` is not on your shell path, reinstall with an explicit interpreter:

```bash
make install-independent PYTHON39=/path/to/python3.9
```

5. Open `/independent/logs` in the browser for the independent-mode error messages

If stuck, run:

```bash
make kill-camera
make run
```

---

## TODO

- Improve frontend with camera status indicator & quality
- Add configurable object buckets beyond `people` and `cat`
- Add richer independent-mode behaviours
