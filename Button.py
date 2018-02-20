#!/usr/bin/env python

import RPi.GPIO as GPIO
import time


class Button(object):
	def __init__(self, pin):
		self.pin = pin
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self.buttonDetect)

	def buttonDetect(self, pin):
		print "detected button pressed "+str(pin)
		return
	
if __name__ == '__main__':
	b = Button(18)
	for i in range(20):
		print i
		time.sleep(1)
	GPIO.cleanup()
