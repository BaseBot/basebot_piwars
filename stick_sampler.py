#!/usr/bin/python2
# Read joystick data and send it over the serial port as packetcomms.Packet()s
# Not pretty, but functional
# Copyright Brian Starkey 2014 <stark3y@gmail.com>
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import joystick
import time
import serial
import sys
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
# These are the only axes we are interested in
axes = [0, 1, 3 ,4, 2, 5]

for axis in axes:
    j.enable(joystick.TYPE_AXIS, axis, True)

last_time = time.time()
then = time.time()
input_tick = 0.05
max_speed = 1.0
dead_zone = 0.30
old_left = 0.0
old_right = 0.0
last_time = time.time()
ev = joystick.Event(0, 0, 0, 0)
resume = True

# Single wrapper for pairs on analogue axes
class ThumbStick:
    def __init__(self, axes = [0, 1], deadzone = dead_zone):
        self.axes = {}
        print "Thumstick, axes {}, dz: {}".format(axes, deadzone)
        for i in axes:
            self.axes[i] = 0.0
        self.deadzone = deadzone * 32768
        print "Deadzone: {}".format(self.deadzone)
        self.range = 32768 - deadzone
        #print "Range: {}".format(self.range)

    def update(self, ev):
        if (ev.evtype == joystick.TYPE_AXIS) and\
                self.axes.has_key(ev.axis):
            val = ev.val
            if abs(val) < self.deadzone:
                val = 0.0
            val = (ev.val / 32768.0)

            self.axes[ev.axis] = val
            return True
        return False

    def value(self):
        x = min(self.axes.keys())
        y = max(self.axes.keys())
        return (self.axes[x], self.axes[y])

# Left thumbstick controls movement, with TelecommandPackets
left_thumbstick = ThumbStick([0, 1], 0.5)
def send_tcmd(now, vals):
    global ser, last_time, resume, old_left, old_right
    x = -vals[1]
    y = vals[0]
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
        # If nothing happened for a while, tell the robot to resume normal
        # task duties
        this_time = time.time()
        if left == 0 and right == 0 and (this_time - last_time) > 3 \
                and not resume:
            ser.write(packetcomms.TextPacket('resume').pack())
            last_time = this_time
            resume = True

# The right thumbstick controls the eye position
right_thumbstick = ThumbStick([3, 4])
def send_eyes(now, vals):
    global ser
    x = (vals[0] / 2) + 0.5
    y = (vals[1] / 2) + 0.5
    pkt = packetcomms.EyeLookPacket(x, y)
    ser.write(pkt.pack())

# The triggers control the eyelid position
triggers = ThumbStick([2, 5])
def send_lids(now, vals):
    global ser
    x = (vals[0] + 1) / 2
    y = (vals[1] + 1) / 2
    pkt = packetcomms.EyeLidPacket(x, y)
    ser.write(pkt.pack())

thumbsticks = {
    'left': (left_thumbstick, send_tcmd),
    'right': (right_thumbstick, send_eyes),
    'trigger': (triggers, send_lids),
}

# Loop forever, checking for events regularly
while 1:
    now = time.time()
    if (now - then >= input_tick):
        then = now
        updates = {}
        while (j.have_events()):
            ev = j.get()
            for name, tup in thumbsticks.iteritems():
                update = tup[0].update(ev)
                if update:
                    updates[name] = tup
                    break;
        for u in updates.values():
            # Do the action. Sorry this is unreadable D:
            u[1](now, u[0].value())

