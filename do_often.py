import math
import smbus
import time

import linesensor
import wallsensor

t = 0.1
i = 0

def do_often(func):
    global t
    next_time = time.time() + t
    while True:
        time_now = time.time()
        if time_now >= next_time:
            next_time = time_now + t
            func()

ws = wallsensor.WallSensor(smbus.SMBus(1), 0x10)

def gnuplot(vals):
    s = ''
    for v in vals:
        s = s +  '{} '.format(v)
    return s

def read_and_print():
    global i
    reading = ws.sense()
    print "{} {}".format(i, reading)
    i = i + 1

do_often(read_and_print)
