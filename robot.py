#!/usr/bin/python2
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import time
import threading
import wheel
from smbus import SMBus
import joystick
import STPacketServer

import logging
logging.basicConfig(filename = 'logfile.log',
        format = '%(asctime)s [%(levelname).4s] %(name)s: %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

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
    "curves": [((1344, 1516), (-60,  -2)),\
               ((1516, 1524), (  -1,  1)),\
               ((1524, 1710), (  2, 60))],
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
    "curves": [((1488, 1308), (-60, -2)),
               ((1308, 1300), (-1, 1)),
               ((1300, 1128), (2, 60))],
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

HOST, PORT = "192.168.0.45", 9000

server = STPacketServer.STServer(HOST, PORT)
ip = server.server_address
port = server.port

server_thread = threading.Thread(target=server.loop)
server_thread.daemon = True
server_thread.start()
print "Server running in: {}".format(server_thread.name)
print "IP: %s Port: %i" % (ip, port)

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


while 1:
    message = server.recv()
    source = message[0]
    packet = message[1]
    if packet.type() == 'tcmd':
        print str(packet)
        left_wheel.set_speed(packet.body.left)
        right_wheel.set_speed(packet.body.right)
        left_wheel.tick()
        right_wheel.tick()


