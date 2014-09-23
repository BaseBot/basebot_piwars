#!/usr/bin/python2
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import time
import threading
import wheel
from smbus import SMBus
import joystick
import time

i2c_bus = SMBus(1)

global_state = {
    "T": 0.5,
    "wheels": { },
}

l_wheel_settings = {
    "i2c_bus": i2c_bus,
    "addr": 0x41,
    "servo": 1,
    "threshold": 0x60,
    "slots": 60,
    "T": global_state["T"],
    # List of pairs of tuples, representing line segments:
    "curves": [((1344, 1516), (-60,  0)),\
               ((1516, 1524), (  0,  0)),\
               ((1524, 1710), (  0, 60))],
}
left_wheel = wheel.Wheel(l_wheel_settings)
global_state["wheels"]["left"] = left_wheel
r_wheel_settings = {
    "i2c_bus": i2c_bus,
    "addr": 0x40,
    "servo": 0,
    "threshold": 0x60,
    "slots": 60,
    "T": global_state["T"],
    "curves": [((1488, 1308), (-60, 0)),
               ((1308, 1300), (0, 0)),
               ((1300, 1128), (0, 60))],
}
right_wheel = wheel.Wheel(r_wheel_settings)
global_state["wheels"]["right"] = right_wheel

class TelemetryServer:
    def __init__(self):
        #self.f = open("%s.log" % str(time.time()), "w")
        pass
    def tick(self):
        global global_state
        #self.f.writelines([str(global_state["wheels"]["left"]) + "\n"])
        print "Left: %s, Right: %s" % (str(global_state["wheels"]["left"]), \
                str(global_state["wheels"]["right"]))
tserv = TelemetryServer()
global_state["tserv"] = tserv

def loop():
    global global_state
    next_time = time.time() + global_state["T"]
    while 1:
        time_now = time.time()
        if (time_now >= next_time):
            next_time = time_now + global_state["T"]
            # Do stuff
            for wheel in global_state["wheels"].values():
                wheel.tick()
            global_state["tserv"].tick()

tick_thread = threading.Thread(target=loop)
tick_thread.daemon = True
tick_thread.start()

#for i in range(900, 1850, 6):
#    left_wheel.set_speed(i)
#    time.sleep(1.5)

def forwards(speed):
    global global_state
    for w in global_state["wheels"].values():
        w.set_speed(speed)
        w.tick()

def f(s):
    forwards(s)

j = joystick.Joystick('/dev/input/js0', False)
axes = { 1: 0, 0: 0 }

for axis in axes.keys():
    j.enable(joystick.TYPE_AXIS, axis, True)

then = time.time()
input_tick = 0.1
turn_epsilon = 20
while 1:
    now = time.time()
    if (now - then >= input_tick):
        then = now
        while (j.have_events()):
            ev = j.get()
            if (ev.evtype == joystick.TYPE_AXIS):
                val = ev.val
                if (abs(val) < 546):
                    val = 0
                axes[ev.axis] = val
        speed = int(axes[1] / 546.133) * -1
        turn = int(axes[0] / 327.68)
        print "Speed: %i, Turn: %i" % (speed, turn)

        left_wheel.set_speed(speed + (turn_epsilon * turn / 100))
        right_wheel.set_speed(speed - (turn_epsilon * turn / 100))
        left_wheel.tick()
        right_wheel.tick()
