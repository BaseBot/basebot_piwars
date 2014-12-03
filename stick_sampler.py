#!/usr/bin/python2
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import joystick
import time
import socket
import packetcomms

host = '10.0.1.166'
port = 9000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host, port))
sock.setblocking(1)

j = joystick.Joystick('/dev/input/js0', False)
axes = { 1: 0, 0: 0 }

for axis in axes.keys():
    j.enable(joystick.TYPE_AXIS, axis, True)

then = time.time()
input_tick = 0.1
max_speed = 1.0
dead_zone = 0.20
old_left = None
old_right = None
last_time = time.time()
ev = joystick.Event(0, 0, 0, 0)
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
        print "now: {}, ev.ts: {}".format(time.time(), ev.ts)
        x = -axes[1]
        y = axes[0]

        left = x + y
        right = x - y
        print "x: {}, y: {}".format(x, y)
        print "Left: {}, Right: {}".format(left, right)
        if (old_left != left) or (old_right != right):
            last_time = time.time()
            old_left = left
            old_right = right
            pkt = packetcomms.TelecommandPacket(left, right)
            sock.sendall(pkt.pack())
        else:
            this_time = time.time()
            if left == 0 and right == 0 and (this_time - last_time) > 3:
                sock.sendall(packetcomms.TextPacket('resume').pack())

