#!/usr/bin/env python

import time
import math
import random
import RPi.GPIO as GPIO
import pigpio
import cherrypy
import StepperMotor
import threading
import Queue

class CatLaser(object):
	def __init__(self, mountHeight, areaWidth, areaLength, motorpins, buttonpins, laserpin):
		#height of the CL above the ground, in inches
		self.mountHeight = mountHeight
		# width and length of area on floor, in inches
		self.areaWidth = areaWidth * 3
		self.areaLength = areaLength * 6
		self._x = 0
		self._y = 0		
		self.buttonpins = buttonpins
		self.button = []
		self.motorpins = motorpins
		self.motor = []
		self.initializeMotors()
		self.initializeButtons()
		self.initializeLaser(laserpin)
		self.runWebUI()
	
	def initializeButtons(self):
		for i, p in enumerate(self.buttonpins):
			self.button.insert(i, Button(p, i, self))
		return
		
	def initializeMotors(self):
		for i, p in enumerate(self.motorpins):
			self.motor.insert(i, StepperMotor.Motor(p, 12, Queue.Queue()))
		return
		
	def initializeLaser(self, pin):
		self.laser = Laser(pin)
		return
	
	
	def goXY(self, x, y):
		self.x = x * self.areaWidth
		self.y = y * self.areaLength + 24.0 # offset area 24inch in front of CatLaser
				
		self._set_angle()
		return
	
	def _set_angle(self):
		[theta, phi] = self.XYtoAngle()
		self.theta = theta
		self.phi = phi
		self.motor[0].queue.put(theta)
		self.motor[1].queue.put(phi)
		return
	
	def XYtoAngle(self):
		x = self.x
		y = self.y
		
		# we use 90+ to center on 90 deg. atan will be -90 to +90. our device cannot move below 0 deg
		theta = 90.0 + math.degrees(math.atan(x/y))
		
		radius = math.sqrt(x**2 + y**2)
		phi = math.degrees(math.atan(radius/self.mountHeight))
		print "x = "+str(x)+", y = "+str(y)
		print "theta = "+str(theta)+", phi = "+str(phi)
		return [theta, phi]
	
	def Pattern(self, patName):
		if(patName == 'traceArea'):
			seq = [
				[0, 0],
				[-.5, 0],
				[-.5, 1],
				[.5, 1],
				[.5, 0],
				[0, 0]
				]
			
		for s in seq:
			self.goXY(s[0], s[1])
			time.sleep(1.5)
		
		return
	
	def goRandom(self):
		self.goXY(random.random(), random.random())
		return
		
	def runWebUI(self):
		cherrypy.config.update({
				'global':{
					'server.socket_host': '0.0.0.0',
					'server.socket_port': 8080,
					'server.environment': "production",
					'engine.autoreload.on': False,
					'log.screen': False
					}
				})
		conf = { '/':
			{ 'tools.staticdir.on': True,
			'tools.staticdir.dir': '/home/pi/catlaser/static'
			}
			}
		cherrypy.tree.mount(Website(self), config = conf)
		cherrypy.engine.start()
		return
		
		
class Button(object):
	def __init__(self, pin, buttonNum, parent):
		self.pin = pin
		self.buttonNum = buttonNum
		self.parent = parent
		
		GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self.buttonDetect)
		#check for button already depressed, b/c event won't fire
		if GPIO.input(self.pin) == GPIO.LOW:
			self.buttonDetect(self.pin)
		return

	def buttonDetect(self, pin):
		print "detected button pressed "+str(pin)
		self.parent.motor[self.buttonNum].hitZero()
		time.sleep(.25) #debounce
		return		

class Laser(object):
	def __init__(self, pin):
		self.pin = pin
		
		#setup pigpio PWM
		self.pi=pigpio.pi()
		self.pi.set_PWM_frequency(self.pin, 100) # Hz
		self.pi.set_PWM_range(self.pin, 100)
		self.brightness = 0
		return

	def set(self, brightness=0):
		self.brightness = brightness
		self.pi.set_PWM_dutycycle(self.pin, brightness)
		return
		
	def shutdown(self):
		self.set(0)
		self.pi.stop()
		return

class Website(object):
	def __init__(self, parent):
		self.parent = parent # pass in the CatLaser so we can access it
		return
		
	@cherrypy.expose
	def index(self):
		#get the user input
		return """<html>
			<head>
			<script src="/jquery-3.1.0.min.js"></script>
			<script src="/catlaser.js"></script>
			<link rel="stylesheet" type="text/css" href="/catlaser.css">
			</head>
			<body>
				<div id="clickbox">
				</div>
			</body>
		</html>"""

	@cherrypy.expose
	def clicked(self, x, y):
		x = float(x)
		y = float(y)
		print "clicked "+str(x)+","+str(y)
		self.parent.goXY(x, y)
		return

if __name__ == '__main__':
	
	GPIO.setmode(GPIO.BCM)

	#    CatLaser(height, width, length, motorpins, buttonpins, laserpin
	cl = CatLaser(32., 36., 36., [[26,19,13,6], [12,16,20,21]], [23, 24], 18)
	
		
	try:
		cl.laser.set(80)
		time.sleep(3)
		cl.Pattern('traceArea')
		#main loop
		while True:
			#cl.goRandom()
			time.sleep(1)
			
	except KeyboardInterrupt:
		print "\n Exiting CatLaser"
		
	finally:
		cl.laser.shutdown()
		for m in cl.motor:
			m.shutdown.set()
		time.sleep(1)
		cherrypy.engine.exit()
		GPIO.cleanup()
