#!/usr/bin/env python

# This code is written by Stephen C Phillips.
# It is in the public domain, so you can do what you like with it
# but a link to http://scphillips.com would be nice.

# It works on the Raspberry Pi computer with the standard Debian Wheezy OS and
# the 28BJY-48 stepper motor with ULN2003 control board.

# Modified by Corey Berman for SIUE ME592 Cat Laser project

from time import sleep
import RPi.GPIO as GPIO
from threading import Thread, Event
import Queue
import math

import logging

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s (%(threadName)-10s) %(message)s',)

class Motor(Thread):
	def __init__(self, pins, rpm, queue, mode=3):
		Thread.__init__(self)
		self.daemon = False
		
		self.P1 = pins[0]
		self.P2 = pins[1]
		self.P3 = pins[2]
		self.P4 = pins[3]
		
		self.mode = mode
		self.deg_per_step = 5.625 / 64  # for half-step drive (mode 3)
		self.steps_per_rev = int(360 / self.deg_per_step)  # 4096
		self.rpm = rpm
		self.zeroed = False
		self.step_angle = 0 
		self.target_angle = 0
		self.queue = queue
		self.shutdown = Event()
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		for p in pins:
			GPIO.setup(p, GPIO.OUT)
			GPIO.output(p, 0)
		
		sleep(1) # wait before starting, let buttons initialize
		self.start()
		return
	
	def run(self):

		while True:
			#check for shutdown
			if self.shutdown.isSet():
				GPIO.cleanup()
				break
			#check the queue
			try:
				q = self.queue.get(False) #get(False) is nonblocking
			except Queue.Empty:
				q = None
			if q == 'shutdown':
				self.shutdown.set()
			if q:
				logging.debug(str(q)+" on the queue")
				self.target_angle = q
				self.queue.task_done()
			if self.zeroed == False:
				self.target_angle = -360

			#move motor
			dif = math.fabs(self.target_angle-self.step_angle)
			if dif > 1:
				nsteps = 1 * (self.target_angle-self.step_angle)/dif
				#logging.debug("move "+str(nsteps)+" steps")
				self.move(nsteps)

		return

	def _set_rpm(self, rpm):
		"""Set the turn speed in RPM."""
		self._rpm = rpm
		# T is the amount of time to stop between signals
		self._T = (60.0 / rpm) / self.steps_per_rev

	# This means you can set "rpm" as if it is an attribute and
	# behind the scenes it sets the _T attribute
	rpm = property(lambda self: self._rpm, _set_rpm)

	def angleToSteps(self, angle):
		"""Take the shortest route to a particular angle (degrees)."""
		# Make sure there is a 1:1 mapping between angle and stepper angle
		target_step_angle = 8 * (int(angle / self.deg_per_step) / 8)
		steps = target_step_angle - self.step_angle
		steps = (steps % self.steps_per_rev)
		if steps > self.steps_per_rev / 2:
			steps -= self.steps_per_rev
		return steps

	def hitZero(self):
		self.step_angle = 0
		self.zeroed = True
		self.moveTo(10)
		return

	def moveTo(self, angle):
		self.queue.put(angle)
		return

	def move(self, steps):
		self._move(steps)
		return

	def __clear(self):
		GPIO.output(self.P1, 0)
		GPIO.output(self.P2, 0)
		GPIO.output(self.P3, 0)
		GPIO.output(self.P4, 0)
		
	def _move(self, big_steps):
		self.__clear()
		if(big_steps>0):
			direction = 'cw'
		else:
			direction = 'acw'
		big_steps = int(math.fabs(big_steps))
		if(direction == 'cw'):
			for i in range(big_steps):
				#print "cw step "+str(i)+"/"+str(big_steps)
				#step 1
				GPIO.output(self.P1, 0)
				GPIO.output(self.P4, 1)
				sleep(self._T)
				#step 2
				GPIO.output(self.P3, 1)
				sleep(self._T)
				#step 3
				GPIO.output(self.P4, 0)
				sleep(self._T)
				#step 4
				GPIO.output(self.P2, 1)
				sleep(self._T)
				#step 5
				GPIO.output(self.P3, 0)
				sleep(self._T)
				#step 6
				GPIO.output(self.P1, 1)
				sleep(self._T)
				#step 7
				GPIO.output(self.P2, 0)
				sleep(self._T)
				#step 8
				GPIO.output(self.P4, 1)
				sleep(self._T)
				self.step_angle = self.step_angle + 1
		else:
			for i in range(big_steps):
				#print "acw step "+str(i)+"/"+str(big_steps)
				#step 1
				GPIO.output(self.P3, 0)
				GPIO.output(self.P4, 1)
				sleep(self._T)
				#step 2
				GPIO.output(self.P1, 1)
				sleep(self._T)
				#step 3
				GPIO.output(self.P4, 0)
				sleep(self._T)
				#step 4
				GPIO.output(self.P2, 1)
				sleep(self._T)
				#step 5
				GPIO.output(self.P1, 0)
				sleep(self._T)
				#step 6
				GPIO.output(self.P3, 1)
				sleep(self._T)
				#step 7
				GPIO.output(self.P2, 0)
				sleep(self._T)
				#step 8
				GPIO.output(self.P4, 1)
				sleep(self._T)
				self.step_angle = self.step_angle - 1
		self.__clear()
		return


if __name__ == "__main__":
	import random
	
	q = Queue.Queue()
	m = Motor([5,6,13,19], 12, q)

	for i in range(10):
		angle = 720*(0.5-random.random())
		logging.debug("angle "+str(angle))
		q.put(angle)
		sleep(2)
	sleep(3)
	m.shutdown.set()
