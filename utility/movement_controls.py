import os
import time

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    from unittest.mock import Mock
    GPIO = Mock()
    GPIO_AVAILABLE = False

# GPIO Pin Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pinMotorAForwards = 10
pinMotorABackwards = 9
pinMotorBForwards = 8
pinMotorBBackwards = 7
PIN_LED = 25

if GPIO_AVAILABLE:
    GPIO.setup([pinMotorAForwards, pinMotorABackwards, pinMotorBForwards, pinMotorBBackwards, PIN_LED], GPIO.OUT)

button_delay = float(os.getenv("BUTTON_DELAY", 0.2))

def Stop():
    GPIO.output([pinMotorAForwards, pinMotorABackwards, pinMotorBForwards, pinMotorBBackwards], 0)

def Forwards():
    print("Moving Forwards")
    GPIO.output(pinMotorAForwards, 1)
    GPIO.output(pinMotorBForwards, 1)
    time.sleep(button_delay)
    Stop()

def Backwards():
    print("Moving Backwards")
    GPIO.output(pinMotorABackwards, 1)
    GPIO.output(pinMotorBBackwards, 1)
    time.sleep(button_delay)
    Stop()

def Left():
    print("Turning Left")
    GPIO.output(pinMotorAForwards, 1)
    GPIO.output(pinMotorBBackwards, 1)
    time.sleep(button_delay)
    Stop()

def Right():
    print("Turning Right")
    GPIO.output(pinMotorABackwards, 1)
    GPIO.output(pinMotorBForwards, 1)
    time.sleep(button_delay)
    Stop()

Stop()
