import os

# Allows for mocking GPIO for testing on a pi that is connected to a monitor
MOCK_GPIO = os.getenv("MOCK_GPIO", "false").lower() == "true"

try:
    if MOCK_GPIO:
        raise ImportError("Mocking GPIO as requested")

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
    print("GPIO is available.")
    GPIO.setup([pinMotorAForwards, pinMotorABackwards, pinMotorBForwards, pinMotorBBackwards, PIN_LED], GPIO.OUT)
    print("GPIO setup completed.")
else:
    print("@@@@@@ GPIO Not detected! Controls will be mocked @@@@@@")

def _set_outputs(active_pins):
    Stop()
    if not active_pins:
        return

    GPIO.output(active_pins, 1)

def Stop():
    GPIO.output([pinMotorAForwards, pinMotorABackwards, pinMotorBForwards, pinMotorBBackwards], 0)

def Forwards():
    print("Moving Forwards")
    _set_outputs([pinMotorAForwards, pinMotorBForwards])

def Backwards():
    print("Moving Backwards")
    _set_outputs([pinMotorABackwards, pinMotorBBackwards])

def Left():
    print("Turning Left")
    _set_outputs([pinMotorAForwards, pinMotorBBackwards])

def Right():
    print("Turning Right")
    _set_outputs([pinMotorABackwards, pinMotorBForwards])

Stop()
