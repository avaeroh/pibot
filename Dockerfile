FROM python:3.9-slim

WORKDIR /app

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y python3-pip python3-rpi.gpio libgl1-mesa-glx libglib2.0-0 curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . /app

# Install Python dependencies
RUN pip install flask python-dotenv flask-socketio opencv-python

# Handle Pi-specific dependencies
COPY handle_pi_specific_dependencies.sh /app/handle_pi_specific_dependencies.sh
RUN /app/handle_pi_specific_dependencies.sh

# TensorFlow Lite installation and model download
RUN pip install -r /app/tflite/requirements.txt

RUN mkdir -p /app/models && \
    curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/object_detection/rpi/lite-model_efficientdet_lite0_detection_metadata_1.tflite' -o /app/models/efficientdet_lite0.tflite && \
    curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/object_detection/rpi/efficientdet_lite0_edgetpu_metadata.tflite' -o /app/models/efficientdet_lite0_edgetpu.tflite

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python3", "app.py"]
