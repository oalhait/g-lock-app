import RPi.GPIO as GPIO 
import time 


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(25,GPIO.OUT)


def LED_on():
	print("LED on")
	GPIO.output(25,GPIO.HIGH)
	time.sleep(1)
	print("LED off")
	GPIO.output(25, GPIO.LOW)
	#hey there hui
