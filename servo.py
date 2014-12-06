# Interface for ServoBlaster servos
# https://github.com/richardghirst/PiBits/tree/master/ServoBlaster
# Copyright Brian Starkey 2014 <stark3y@gmail.com>
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import os

class Servo:
	def __init__(self, servonum):
		self.servonum = servonum

	def set_us(self, us):
		os.system("echo %i=%ius > /dev/servoblaster" % (self.servonum, us))

	def set_pc(self, pos):
		if (pos > 1):
			pos = 1
		elif (pos < 0):
			pos = 0
		pos = pos * 100
		os.system("echo %i=%i%% > /dev/servoblaster" % (self.servonum, pos))

	def off(self):
		os.system("echo %i=0 > /dev/servoblaster" % self.servonum)

