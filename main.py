#!/usr/bin/python

import logging
import math
import os
import smbus
import threading

import classrobot
import linesensor
import linetask
import serialsocket
import tanksteer
import waypointtask
import wallsensor
import walltask

def initLogging(settings):
    formatter = logging.Formatter(\
            '%(asctime)s [%(levelname).4s] %(name)s: %(message)s')
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(
            settings['logging_settings']['file'])
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # If possible, open a fifo logger at a lower verbosity for realtime status
    if settings['logging_settings'].has_key('fifo'):
        try:
            fd = os.open(settings['logging_settings']['fifo'],\
                    os.O_WRONLY | os.O_NONBLOCK)
            f = os.fdopen(fd, 'w')
            fifo_handler = logging.StreamHandler(f)
            fifo_handler.setLevel(logging.INFO)
            fifo_handler.setFormatter(formatter)
            root_logger.addHandler(fifo_handler)
        except Exception as e:
            root_logger.warning("Couldn't open fifo: {}".format(e))

i2c_bus = smbus.SMBus(1)
settings = {
    'tau': 0.1,
    'platform': {
        'chassis': tanksteer.Tanksteer,
        # TODO: Describe buses here
    },
    'logging_settings': {
        'fifo': 'logfifo',
        'file': 'logfile.log',
    },
    'server_settings': {
        'host': "10.0.1.166",
        'port': 9000,
    },
    'serial_settings': {
        'port': '/dev/ttyAMA0',
        'baud': 115200,
        'enable': True,
    },
    'chassis_settings': {
        'tau': 0.08,
        'chassis_width': 160.0,
        'wheel_diameter': 69.8,
        'speed_limiter': 1.0,
        'wheel_settings': {
            'left': {
                # TODO: Get bus instances from platform
                'i2c_bus': i2c_bus,
                'addr': 0x41,
                'servo': 0,
                'threshold': 0x40,
                'slots': 60,
                'curves': [((1413, 1470), (-100,  -1)),\
                           ((1471, 1479), (  0,  0)),\
                           ((1488, 1536), (  1, 100))],
            },
            'right': {
                'i2c_bus': i2c_bus,
                'addr': 0x40,
                'servo': 1,
                'threshold': 0x40,
                'slots': 60,
                'curves': [((1540, 1480), (-100, -1)),
                           ((1479, 1471), (0, 0)),
                           ((1471, 1417), (1, 100))],
            },
        },
    },
    'sensors': {
        'LineSensor': linesensor.LineSensor(i2c_bus, 0x10),
        'WallSensor': wallsensor.WallSensor(i2c_bus, 0x10),
    }
}

initLogging(settings)
robo = classrobot.Robot(settings)
# If required, start listening on the serial port
if settings['serial_settings']['enable']:
    serial = serialsocket.SerialSocket(settings)
    serial_thread = threading.Thread(target=serial.loop)
    serial_thread.daemon = True
    serial_thread.start()
    logging.info("Serial socket running in thread {}".format(serial_thread))


# Task function "macros"
def square():
    global robo
    robo.task = waypointtask.WaypointTask()
    wp = { 'position': (0, 1000), 'heading': math.pi / 2 }
    robo.task.add_waypoint(wp)
    wp = { 'position': (1000, 1000), 'heading': 0.0 }
    robo.task.add_waypoint(wp)
    wp = { 'position': (1000, 0), 'heading': -math.pi / 2 }
    robo.task.add_waypoint(wp)
    wp = { 'position': (0, 0), 'heading': math.pi }
    robo.task.add_waypoint(wp)
    robo.loop()

def tpt():
    global robo
    robo.task = waypointtask.WaypointTask()
    robo.chassis.max_speed = 50
    waypoints = [
        { 'position': (0, 1495), 'heading': math.pi / 2 },
        { 'position': (-800, 1495), 'heading': math.pi },
        { 'position': (800, 1495), 'heading': math.pi,\
            'approach_backwards': True },
        { 'position': (0, 1495), 'heading': math.pi },
        #FIXME: Have to bodge the endpoint a bit...
        { 'position': (200, 0), 'heading': -math.pi / 2 },
    ]
    [robo.task.add_waypoint(wp) for wp in waypoints]
    robo.loop()

def linefollow():
    global robo
    robo.task = linetask.LineFollowerTask()
    robo.chassis.max_speed = 70
    logging.info("Starting sensor value: {}".format(\
            robo.sensors['LineSensor'].read()))
    robo.loop()

def wall(thresh = 100, speed = 0.3):
    global robo
    robo.task = walltask.WallTask(thresh, speed)
    robo.loop()

def stop():
    robo.chassis.stop()
