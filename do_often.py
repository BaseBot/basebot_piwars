import math
import smbus
import time

import linesensor

t = 0.3
i = 0

def do_often(func):
    next_time = time.time() + t
    while True:
        time_now = time.time()
        if time_now >= next_time:
            func()

ls = linesensor.LineSensor(smbus.SMBus(1), 0x10)

def gnuplot(vals):
    s = ''
    for v in vals:
        s = s +  '{} '.format(v)
    return s

def read_and_print():
    global i
    centroid =  ls.find_line()
    print "{} {}".format(i, centroid)
    i = i + 1

do_often(read_and_print)
