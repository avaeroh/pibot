#!/bin/bash

# Check if the system is a Raspberry Pi
if grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "Running on a Raspberry Pi. Installing picamera..."
    pip install picamera
else
    echo "Not running on a Raspberry Pi. Skipping picamera installation..."
fi

# Install other dependencies
