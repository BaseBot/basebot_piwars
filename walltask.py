# Task for driving straight until a wall gets in the way
# Copyright Brian Starkey 2014 <stark3y@gmail.com>

import logging
import math
import random

class WallTask:
    def __init__(self, threshold = 100, speed = 0.1):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.threshold = 100
        self.default_speed = speed
        self.odometer = None

    def plan(self, readings):
        if self.odometer == None:
            self.odometer = readings['odometer']

        if readings['WallSensor'] < self.threshold:
            return { 'manual': (0, 0) }

        wheel_moved = (readings['odometer'][0] - self.odometer[0],
                readings['odometer'][1] - self.odometer[1])

        # FIXME: At an hour's notice, this is the best way I can think of of
        # driving a straight line
        if wheel_moved[0] > wheel_moved[1]:
            return { 'manual': (0, self.default_speed) }
        elif wheel_moved[1] > wheel_moved[0]:
            return { 'manual': (self.default_speed, 0) }
        else:
            return { 'manual': (self.default_speed, self.default_speed) }

