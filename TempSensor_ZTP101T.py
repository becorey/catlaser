import time
import spidev
import os
import math

class TempSensor_ZTP101T(object):
	def __init__(self, vref=5*1100.0/327000.0):
		self.spi = spidev.SpiDev()
		self.spi.open(0,0)
		self.spi.max_speed_hz = 250000
		self.vref=vref

		
	def readadc(self, npins=2):
		"Reads SPI data from MCP3008 chip. npins must be integer 0-7"
		data = [False for i in range(0, npins)]
		for pin in range(0,npins):
			adc = self.spi.xfer2([1, (8+pin)<<4, 0])
			data[pin] = ((adc[1]&3) << 8) + adc[2]
		self.adc = data
		print data
		return data

		
	def convertVolts(self, data, places=6):
		"Converts data to voltage level"
		volts = (data * self.vref) / 1023.0
		volts = round(volts,places)
		print "V ="+str(volts)
		return volts
				
	def readRemote(self, channel):
		r = self.adc[channel]
		mV = self.convertVolts(r)*1000.0
		#determined from datasheet graph and polynomial regression
		# object Temperature at T_amb = 25 C
		T = (0.2887921)*mV**3 - 2.979967*mV**2 + 22.87922*mV + 23.07406981
		return round(T,3)
		
	def readThermistor(self, channel, Rdiv = 9880):
		#uses a voltage divider. 
		# Vin = Vref
		# Vout = read from adc
		# R1 = Rdiv
		# R2 = calculated
		Vout = self.convertVolts(self.adc[channel])
		#calculate R from voltage divider
		# Vout = Vin * R2/(R1+R2)
		# R2 = Vout*R1/(Vin-Vout)
		print "vref = "+str(self.vref)
		print "Vout = "+str(Vout)
		R2 = Vout*Rdiv/(self.vref-Vout)
		if R2 <= 0 :
			R2 = .001
		print "R2 = "+str(R2)
		#calculate T_amb from R
		# eqn determined from datasheet and log regression
		# only valid from 0 C to 100 C
		T = -26.0207442*math.log(R2) + 85.86349099
		return T

if __name__ == '__main__':
  
    tempSensor = TempSensor_ZTP101T()
    for i in range(0,50):
		tempSensor.readadc()
		print "Remote Temp = "+str(tempSensor.readRemote(0))
		print "Local Temp = "+str(tempSensor.readThermistor(1))
		time.sleep(.5)

		
