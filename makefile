.PHONY: all setup install-deps install-python-deps install-independent-python-deps download-models run run-control run-independent test clean setup-pipe stream kill-camera

VENV_DIR := .venv
MODEL_DIR := models
FIFO_PATH := /tmp/vidstream.mjpeg

all: setup install-deps install-python-deps install-independent-python-deps

setup:
	@echo "[Setup] Creating app directory structure"
	mkdir -p $(MODEL_DIR)

install-deps:
	@echo "[System] Updating apt and installing system dependencies"
	sudo apt-get update
	sudo apt-get install -y \
		curl gnupg \
		python3-pip python3-rpi.gpio \
		libgl1-mesa-glx libglib2.0-0 \
		v4l-utils python3-opencv libcamera-apps

	@echo "[Keys] Installing Raspberry Pi GPG keys"
	curl -fsSL https://archive.raspberrypi.org/debian/raspberrypi.gpg.key | \
		gpg --dearmor | \
		sudo tee /usr/share/keyrings/raspberrypi-archive-keyring.gpg > /dev/null

	@echo "[Repo] Adding Raspberry Pi repository"
	echo "deb [signed-by=/usr/share/keyrings/raspberrypi-archive-keyring.gpg] http://archive.raspberrypi.org/debian bookworm main" | \
		sudo tee /etc/apt/sources.list.d/raspi.list > /dev/null

	@echo "[System] Cleaning up apt"
	sudo apt-get clean

install-python-deps:
	@echo "[Python] Checking for existing virtual environment"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "[Python] Creating virtual environment in $(VENV_DIR)"; \
		python3 -m venv $(VENV_DIR); \
	else \
		echo "[Python] Virtual environment already exists"; \
	fi

	@echo "[Python] Installing dependencies"
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt

install-independent-python-deps:
	@echo "[Python] Installing independent mode dependencies"
	$(VENV_DIR)/bin/pip install -r tflite/requirements.txt

download-models:
	@echo "[Model] Downloading TensorFlow Lite models"
	curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/object_detection/rpi/lite-model_efficientdet_lite0_detection_metadata_1.tflite' -o $(MODEL_DIR)/efficientdet_lite0.tflite
	curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/object_detection/rpi/efficientdet_lite0_edgetpu_metadata.tflite' -o $(MODEL_DIR)/efficientdet_lite0_edgetpu.tflite

run:
	@echo "[Run] Starting application"
	PYTHONUNBUFFERED=1 PYTHONPATH=$(PWD) $(VENV_DIR)/bin/python main.py

run-control:
	@echo "[Run] Starting pibot in control mode"
	PYTHONUNBUFFERED=1 PYTHONPATH=$(PWD) PIBOT_MODE=control $(VENV_DIR)/bin/python main.py

run-independent:
	@echo "[Run] Starting pibot in independent mode"
	PYTHONUNBUFFERED=1 PYTHONPATH=$(PWD) PIBOT_MODE=independent $(VENV_DIR)/bin/python main.py

test:
	@echo "[Test] Running test suite with mocked Pi hardware"
	PYTHONPATH=$(PWD) MOCK_GPIO=true PYTHONPYCACHEPREFIX=/tmp/pycache $(VENV_DIR)/bin/python -m pytest

setup-pipe:
	@echo "[Pipe] Creating video stream FIFO if missing"
	@if [ ! -p $(FIFO_PATH) ]; then \
		mkfifo $(FIFO_PATH); \
		echo "FIFO created at $(FIFO_PATH)"; \
	else \
		echo "FIFO already exists"; \
	fi

stream:
	@echo "[Stream] Starting Raspberry Pi camera stream"
	@if command -v rpicam-vid >/dev/null 2>&1; then \
		rpicam-vid -t 0 --codec mjpeg --inline --width 640 --height 480 -o $(FIFO_PATH); \
	else \
		libcamera-vid -t 0 --codec mjpeg --inline --width 640 --height 480 -o $(FIFO_PATH); \
	fi

kill-camera:
	@echo "[Cleanup] Killing all camera streaming processes"
	-pkill -f 'rpicam-vid|libcamera-vid' || true

clean:
	@echo "[Clean] Removing model files and FIFO"
	rm -rf $(MODEL_DIR)
	@if [ -p $(FIFO_PATH) ]; then rm $(FIFO_PATH); fi
