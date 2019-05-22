import RPi.GPIO as GPIO 
import time 
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(20,GPIO.OUT)
print("strike on")
GPIO.output(20,GPIO.HIGH)
time.sleep(50)
print("strike off")
GPIO.output(20, GPIO.LOW)
GPIO.cleanup()
