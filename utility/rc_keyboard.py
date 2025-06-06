# CamJam EduKit 3 - Robotics
import RPi.GPIO as GPIO 
import time 

# Set the GPIO modes
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set variables for the GPIO motor pins
pinMotorAForwards = 10
pinMotorABackwards = 9
pinMotorBForwards = 8
pinMotorBBackwards = 7

# Set the GPIO Pin mode
GPIO.setup(pinMotorAForwards, GPIO.OUT)
GPIO.setup(pinMotorABackwards, GPIO.OUT)
GPIO.setup(pinMotorBForwards, GPIO.OUT)
GPIO.setup(pinMotorBBackwards, GPIO.OUT)

# Turn all motors off
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
import sys, termios, tty, os

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

PIN_LED = 25
GPIO.setup(PIN_LED, GPIO.OUT)
GPIO.output(PIN_LED, 0)
button_delay = 0.2

for x in range(0,3):
    GPIO.output(PIN_LED, 1)
    time.sleep(0.25)
    GPIO.output(PIN_LED, 0)
    time.sleep(0.25)

while True:
    char = getch()

    if (char == "q"):
        StopMotors()
        exit(0)  

    if (char == "a"):
        print('Left pressed')
        Left()
        time.sleep(button_delay)

    if (char == "d"):
        print('Right pressed')
        Right()
        time.sleep(button_delay)          

    elif (char == "w"):
        print('Up pressed')
        Forwards()       
        time.sleep(button_delay)          
    
    elif (char == "s"):
        print('Down pressed') 
        Backwards()
        time.sleep(button_delay)  
    
    StopMotors()
