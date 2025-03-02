FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3-pip python3-rpi.gpio libgl1-mesa-glx libglib2.0-0 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install flask python-dotenv flask-socketio opencv-python

# Can't install picamera on a non-Raspberry Pi - so handling this for external development
COPY handle_pi_specific_dependencies.sh /app/handle_pi_specific_dependencies.sh
RUN /app/handle_pi_specific_dependencies.sh

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python3", "app.py"]