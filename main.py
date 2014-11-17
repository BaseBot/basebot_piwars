#!/usr/bin/python

import logging
import threading

import classrobot

logging.basicConfig(filename = 'logfile.log',
        format = '%(asctime)s [%(levelname).4s] %(name)s: %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)


settings = {
    'host': "192.168.0.45",
    'port': 9000,
    'tau': 1,
}

robo = classrobot.Robot(settings)
