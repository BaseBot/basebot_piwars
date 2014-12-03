#!/usr/bin/python2
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import joystick
import time
import serial
import socket
import packetcomms

ser = serial.Serial()
ser.port     = '/dev/ttyUSB0'
ser.baudrate = 115200
ser.timeout  = 1     # required so that the reader thread can exit

try:
    ser.open()
except serial.SerialException, e:
    sys.stderr.write("Could not open serial port %s: %s\n" % \
            (ser.portstr, e))
    sys.exit(1)

j = joystick.Joystick('/dev/input/js0', False)
axes = { 1: 0, 0: 0 }

for axis in axes.keys():
    j.enable(joystick.TYPE_AXIS, axis, True)

last_time = time.time()
then = time.time()
input_tick = 0.05
max_speed = 1.0
dead_zone = 0.20
old_left = 0.0
old_right = 0.0
last_time = time.time()
ev = joystick.Event(0, 0, 0, 0)
resume = True
while 1:
    now = time.time()
    if (now - then >= input_tick):
        then = now
        while (j.have_events()):
            ev = j.get()
            if (ev.evtype == joystick.TYPE_AXIS):
                val = ev.val / 32768.0
                if (abs(val) < dead_zone):
                    val = 0
                axes[ev.axis] = val
        x = -axes[1]
        y = axes[0]

        left = x + y
        right = x - y
        #print "x: {}, y: {}".format(x, y)
        #print "Left: {}, Right: {}".format(left, right)
        if (old_left != left) or (old_right != right):
            last_time = time.time()
            old_left = left
            old_right = right
            pkt = packetcomms.TelecommandPacket(left, right)
            ser.write(pkt.pack())
            resume = False
        else:
            this_time = time.time()
            if left == 0 and right == 0 and (this_time - last_time) > 3 \
                    and not resume:
                ser.write(packetcomms.TextPacket('resume').pack())
                last_time = this_time
                resume = True

