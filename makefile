.PHONY: all setup install-deps install-python-deps download-models run clean setup-pipe stream kill-camera

VENV_DIR := .venv
MODEL_DIR := models
FIFO_PATH := /tmp/vidstream.mjpeg

all: setup install-deps install-python-deps

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

download-models:
	@echo "[Model] Downloading TensorFlow Lite models"
	curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/object_detection/rpi/lite-model_efficientdet_lite0_detection_metadata_1.tflite' -o $(MODEL_DIR)/efficientdet_lite0.tflite
	curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/object_detection/rpi/efficientdet_lite0_edgetpu_metadata.tflite' -o $(MODEL_DIR)/efficientdet_lite0_edgetpu.tflite

run:
	@echo "[Run] Starting application"
	PYTHONUNBUFFERED=1 PYTHONPATH=$(PWD) $(VENV_DIR)/bin/python app.py

setup-pipe:
	@echo "[Pipe] Creating video stream FIFO if missing"
	@if [ ! -p $(FIFO_PATH) ]; then \
		mkfifo $(FIFO_PATH); \
		echo "FIFO created at $(FIFO_PATH)"; \
	else \
		echo "FIFO already exists"; \
	fi

stream:
	@echo "[Stream] Starting libcamera-vid"
	libcamera-vid -t 0 --inline --width 640 --height 480 -o $(FIFO_PATH)

kill-camera:
	@echo "[Cleanup] Killing all libcamera-vid processes"
	-pkill -f libcamera-vid || true

clean:
	@echo "[Clean] Removing model files and FIFO"
	rm -rf $(MODEL_DIR)
	@if [ -p $(FIFO_PATH) ]; then rm $(FIFO_PATH); fi
