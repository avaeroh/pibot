.PHONY: all setup install-deps install-python39-build-deps install-python39 bootstrap-independent install-control-python-deps install-independent-python-deps install-control install-independent download-models run run-control run-independent test clean setup-pipe stream kill-camera

VENV_CONTROL := .venv-control
VENV_INDEPENDENT := .venv-independent
VENV_LEGACY := .venv
PYTHON39 ?= python3.9
MODEL_DIR := models
FIFO_PATH := /tmp/vidstream.mjpeg

ifeq ($(wildcard $(VENV_CONTROL)/bin/python),)
CONTROL_PYTHON := $(VENV_LEGACY)/bin/python
else
CONTROL_PYTHON := $(VENV_CONTROL)/bin/python
endif

all: setup install-deps install-control install-independent

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

install-python39-build-deps:
	@echo "[System] Installing build dependencies for Python 3.9 via pyenv"
	sudo apt-get update
	sudo apt-get install -y \
		build-essential curl git \
		libssl-dev zlib1g-dev libbz2-dev \
		libreadline-dev libsqlite3-dev libncursesw5-dev \
		xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

install-python39:
	@echo "[Python] Installing Python 3.9 via pyenv (opt-in bootstrap)"
	@command -v git >/dev/null 2>&1 || (echo "[Python] git is required for pyenv bootstrap." && exit 1)
	@if [ ! -d "$$HOME/.pyenv" ]; then \
		echo "[Python] Cloning pyenv into $$HOME/.pyenv"; \
		git clone https://github.com/pyenv/pyenv.git $$HOME/.pyenv; \
	else \
		echo "[Python] pyenv already exists at $$HOME/.pyenv"; \
	fi
	@PYENV_ROOT="$$HOME/.pyenv" PATH="$$HOME/.pyenv/bin:$$PATH" pyenv install -s 3.9.19
	@echo "[Python] Python 3.9 installed at $$HOME/.pyenv/versions/3.9.19/bin/python3.9"

bootstrap-independent: install-python39-build-deps install-python39
	@echo "[Python] Bootstrapping independent mode with pyenv-managed Python 3.9"
	$(MAKE) install-independent PYTHON39=$$HOME/.pyenv/versions/3.9.19/bin/python3.9

install-control-python-deps:
	@echo "[Python] Checking for existing control virtual environment"
	@if [ ! -d "$(VENV_CONTROL)" ]; then \
		echo "[Python] Creating control virtual environment in $(VENV_CONTROL)"; \
		python3 -m venv $(VENV_CONTROL); \
	else \
		echo "[Python] Control virtual environment already exists"; \
	fi

	@echo "[Python] Installing control-mode dependencies"
	$(VENV_CONTROL)/bin/pip install --upgrade pip
	$(VENV_CONTROL)/bin/pip install -r requirements.txt

install-independent-python-deps:
	@echo "[Python] Checking for existing independent virtual environment"
	@command -v $(PYTHON39) >/dev/null 2>&1 || (echo "[Python] Could not find $(PYTHON39). Install Python 3.9 first or run 'make install-independent PYTHON39=/path/to/python3.9'." && exit 1)
	@if [ ! -d "$(VENV_INDEPENDENT)" ]; then \
		echo "[Python] Creating independent virtual environment in $(VENV_INDEPENDENT)"; \
		$(PYTHON39) -m venv $(VENV_INDEPENDENT); \
	else \
		echo "[Python] Independent virtual environment already exists"; \
	fi

	@echo "[Python] Installing independent-mode dependencies"
	$(VENV_INDEPENDENT)/bin/pip install --upgrade pip
	$(VENV_INDEPENDENT)/bin/pip install -r requirements.txt
	$(VENV_INDEPENDENT)/bin/pip install -r tflite/requirements.txt

install-control: install-control-python-deps

install-independent: install-independent-python-deps

download-models:
	@echo "[Model] Downloading TensorFlow Lite models"
	curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/object_detection/rpi/lite-model_efficientdet_lite0_detection_metadata_1.tflite' -o $(MODEL_DIR)/efficientdet_lite0.tflite
	curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/object_detection/rpi/efficientdet_lite0_edgetpu_metadata.tflite' -o $(MODEL_DIR)/efficientdet_lite0_edgetpu.tflite

run:
	@echo "[Run] Starting application with control environment"
	PYTHONUNBUFFERED=1 PYTHONPATH=$(PWD) PIBOT_MODE=control $(CONTROL_PYTHON) main.py

run-control:
	@echo "[Run] Starting pibot in control mode"
	PYTHONUNBUFFERED=1 PYTHONPATH=$(PWD) PIBOT_MODE=control $(CONTROL_PYTHON) main.py

run-independent:
	@echo "[Run] Starting pibot in independent mode"
	PYTHONUNBUFFERED=1 PYTHONPATH=$(PWD) PIBOT_MODE=independent $(VENV_INDEPENDENT)/bin/python main.py

test:
	@echo "[Test] Running test suite with mocked Pi hardware"
	PYTHONPATH=$(PWD) MOCK_GPIO=true PYTHONPYCACHEPREFIX=/tmp/pycache $(CONTROL_PYTHON) -m pytest

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
