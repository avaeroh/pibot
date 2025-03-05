FROM python:3.11-slim

WORKDIR /app

# Install required tools
RUN apt-get update && \
    apt-get install -y curl gnupg

# Add Raspberry Pi OS GPG key
RUN curl -fsSL https://archive.raspberrypi.org/debian/raspberrypi.gpg.key | gpg --dearmor -o /usr/share/keyrings/raspberrypi-archive-keyring.gpg

# Add Raspberry Pi OS repository with signed-by option
RUN echo "deb [signed-by=/usr/share/keyrings/raspberrypi-archive-keyring.gpg] http://archive.raspberrypi.org/debian bookworm main" | tee /etc/apt/sources.list.d/raspi.list

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y python3-pip python3-rpi.gpio libgl1-mesa-glx libglib2.0-0 curl v4l-utils python3-picamera2 libcamera-apps && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . /app

# Install Python dependencies
RUN pip install flask python-dotenv flask-socketio opencv-python "numpy<2"
# COPY requirements.txt /app/requirements.txt
# RUN pip install -r requirements.txt

# Handle Pi-specific dependencies
COPY handle_pi_specific_dependencies.sh /app/handle_pi_specific_dependencies.sh
RUN /app/handle_pi_specific_dependencies.sh

# TensorFlow Lite installation and model download
RUN pip install -r /app/tflite/requirements.txt

# RUN mkdir -p /app/models && \
#     curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/object_detection/rpi/lite-model_efficientdet_lite0_detection_metadata_1.tflite' -o /app/models/efficientdet_lite0.tflite && \
#     curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/object_detection/rpi/efficientdet_lite0_edgetpu_metadata.tflite' -o /app/models/efficientdet_lite0_edgetpu.tflite

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose default Flask port
EXPOSE 5000

CMD ["python3", "app.py"]
