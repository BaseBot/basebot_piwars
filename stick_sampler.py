#!/usr/bin/python2
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import Packet
import joystick
import time
import socket
import STPacketServer

host = '192.168.0.45'
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
turn_epsilon = 20
max_speed = 60
divisor = 32768.0 / max_speed;
dead_zone = 0.20
old_left = None
old_right = None
while 1:
    now = time.time()
    if (now - then >= input_tick):
        then = now
        while (j.have_events()):
            ev = j.get()
            if (ev.evtype == joystick.TYPE_AXIS):
                val = ev.val
                if (abs(val) < (32768 * dead_zone)):
                    val = 0
                axes[ev.axis] = val
        speed = int(axes[1] / divisor) * -1
        turn = int(axes[0] / 327.68)
        print "Speed: %i, Turn: %i" % (speed, turn)
        left = speed + (turn_epsilon * turn / 100)
        right = speed - (turn_epsilon * turn / 100)
        if (old_left != left) or (old_right != right):
            old_left = left
            old_right = right
            pkt = Packet.TelecommandPacket(left, right)
            sock.sendall(pkt.pack())

