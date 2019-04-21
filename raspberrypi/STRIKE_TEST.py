import RPi.GPIO as GPIO 
import time 
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(26,GPIO.OUT)
print("strike on")
GPIO.output(26,GPIO.HIGH)
time.sleep(5)
print("strike off")
GPIO.output(26, GPIO.LOW)
GPIO.cleanup()
