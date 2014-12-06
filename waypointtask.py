# Task for driving between waypoints in cartesian space
# Copyright Brian Starkey 2014 <stark3y@gmail.com>

import logging
import math
import Queue

class WaypointTask():
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("WaypointTask init")
        self.waypoints = Queue.Queue()
        # How close to a waypoint do we need to get?
        self.arrived_radius = 50
        # How close does our heading have to match at a waypoint?
        self.arrived_d_theta = math.pi / 8
        self.current_waypoint = None

    def add_waypoint(self, waypoint):
        if not self.current_waypoint:
            self.current_waypoint = waypoint
        else:
            self.waypoints.put(waypoint)

    def next_waypoint(self):
        if self.waypoints.empty():
            self.current_waypoint = None
        else:
            self.current_waypoint = self.waypoints.get()

    def distance(self, readings):
        t_pos = self.current_waypoint['position']
        c_pos = readings['position']
        distance = (t_pos[0] - c_pos[0], t_pos[1] - c_pos[1])
        return distance

    # Did we arrive?
    def arrived(self, readings):
        if not self.current_waypoint:
            return True
        distance = self.distance(readings)
        radius = math.sqrt(distance[0]**2 + distance[1]**2)
        d_theta = self.current_waypoint['heading'] - readings['heading']
        self.logger.debug("Distance to wp: %.2f, heading: %2.4f",
                radius, d_theta)

        if (abs(radius) <= self.arrived_radius) and \
                (abs(d_theta) < self.arrived_d_theta):
            return True
        return False

    def clamp_theta(self, theta):
        if (theta > math.pi):
            return theta - (2 * math.pi)
        elif (theta < -math.pi):
            return theta + (2 * math.pi)
        else:
            return theta

    # Task plan routine - what's next?!
    def plan(self, readings):
        distance = 0.0
        d_theta = 0.0
        if self.current_waypoint:
            if self.arrived(readings):
                self.logger.info("Waypoint {} reached".format(\
                    self.current_waypoint))
                self.next_waypoint()
            else:
                vector = self.distance(readings)
                distance = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
                if (distance > self.arrived_radius):
                    vector_angle = math.atan2(vector[1], vector[0])
                    d_theta = vector_angle - readings['heading']
                    wp = self.current_waypoint
                    if wp.has_key('approach_backwards') and \
                            wp['approach_backwards'] == True:
                        d_theta = d_theta + math.pi
                        distance = -distance
                else:
                    d_theta = self.current_waypoint['heading'] - \
                            readings['heading']
            d_theta = self.clamp_theta(d_theta)

        return {
            'd_theta': d_theta,
            'distance': distance,
        }

