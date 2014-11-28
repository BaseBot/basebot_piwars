#!/usr/bin/python

import logging
import math
import smbus
import threading

import classrobot
import linesensor
import tanksteer

logging.basicConfig(filename = 'logfile.log',
        format = '%(asctime)s [%(levelname).4s] %(name)s: %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

i2c_bus = smbus.SMBus(1)

settings = {
    'tau': 0.1,
    'platform': {
        'chassis': tanksteer.Tanksteer,
        # TODO: Describe buses here
    },
    'server_settings': {
        'host': "192.168.0.21",
        'port': 9000,
    },
    'chassis_settings': {
        'tau': 0.08,
        'chassis_width': 160.0,
        'wheel_diameter': 69.8,
        'speed_limiter': 0.9,
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
    }
}

robo = classrobot.Robot(settings)

def square():
    global robo
    wp = { 'position': (0, 1000), 'heading': math.pi / 2 }
    robo.task.add_waypoint(wp)
    wp = { 'position': (1000, 1000), 'heading': 0.0 }
    robo.task.add_waypoint(wp)
    wp = { 'position': (1000, 0), 'heading': -math.pi / 2 }
    robo.task.add_waypoint(wp)
    wp = { 'position': (0, 0), 'heading': math.pi }
    robo.task.add_waypoint(wp)
    robo.loop()
