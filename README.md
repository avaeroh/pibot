# pibot

My robot Pi! This has been built with:

- Raspberry Pi 4B  
- CamJam EduKit #3 (motor controller + GPIO)  
- 10,000mAh power bank (for Pi)  
- 4x AA batteries (for motors)  
- PiCamera (note: IR version has not worked reliably)

---

## Current Functionality

- Flask-based webserver for PiCamera streaming and WASD/button control  
- Real-time video streaming using `libcamera-vid` 
- Graceful teardown of camera processes and cleanup on exit  
- Automatic install/run via Makefile
- Can be developed against without GPIO functionality (utilising a mocked import of GPIO)

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

### 1. (Optional) Create a `.env` file to overwrite config.

```env
PYTHONUNBUFFERED=1
BUTTON_DELAY=0.2
FLASK_PORT=5000
LIBCAM_FPS=10
LIBCAM_QUALITY=85
LIBCAM_ROTATION=180 # Depending on which way up your camera is
```

---

### 2. Install dependencies

```bash
make all
```

Installs system tools, Python packages, and prepares folders.

---

### 3. Run the Flask app

```bash
make run
```

This will:

- Start `libcamera-vid` in the background
- Stream frames through a named pipe (`/tmp/vidstream.mjpeg`)
- Serve the control interface via Flask + WebSocket
- Expose logs via `/logs` for debugging

---

### 4. (Optional) Download TensorFlow Lite models

```bash
make download-models
```

Places `.tflite` files in the `models/` folder.

---

### 5. Clean up (including FIFO and models)

```bash
make clean
```

---

## Developer Notes

- All video is streamed over WebSocket using base64 JPEG frames  
- The camera feed is managed using `libcamera-vid`, started and cleaned up by the Flask server  
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
