#!/usr/bin/python2
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import math

class Localiser:
    def __init__(self, b, odometer):
        self.b = b
        self.reset(odometer)

    def reset(self, odometer):
        self.last = odometer
        self.theta = 0.0
        self.pos = (0, 0)

    def update(self, odometer):
        distance_moved = (odometer[0] - self.last[0], \
                odometer[1] - self.last[1])
        # TODO: Improve the fuzzyness here
        if (abs(distance_moved[0] - distance_moved[1]) < 
                (0.05 * abs(distance_moved[0] + distance_moved[1]))):
            delta_theta = 0.0
            delta_s = (-distance_moved[1] * math.sin(self.theta), \
                       distance_moved[1] * math.cos(self.theta))
        else:
            turn_r = (self.b / 2) * ((distance_moved[1] + distance_moved[0]) / \
                    (distance_moved[1] - distance_moved[0]))
            delta_theta = (distance_moved[1] - distance_moved[0]) / self.b
            delta_x = -turn_r * \
                    (math.sin(delta_theta + self.theta) - math.sin(self.theta))
            delta_y = -turn_r * \
                    (math.cos(delta_theta + self.theta) - math.cos(self.theta))
            delta_s = (delta_x, delta_y)
        self.last = odometer
        self.pos = (self.pos[0] + delta_s[0], self.pos[1] + delta_s[1])
        self.theta = self.theta + delta_theta

