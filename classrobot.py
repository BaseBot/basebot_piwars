#!/usr/bin/python

import logging
import math
import Queue
import smbus
import time
import threading

import packetcomms

class WaypointTask():
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("WaypointTask init")
        self.waypoints = Queue.Queue()
        self.arrived_radius = 50
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
                print "sqrt: {}".format(distance)
                if (distance > self.arrived_radius):
                    vector_angle = math.atan2(vector[1], vector[0])
                    d_theta = vector_angle - readings['heading']
                else:
                    d_theta = self.current_waypoint['heading'] - \
                            readings['heading']
            d_theta = self.clamp_theta(d_theta)

        return {
            'd_theta': d_theta,
            'distance': distance,
        }


class Robot():
    def __init__(self, settings):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Robot init")

        self.tau = settings['tau']

        chassis_t = settings['platform']['chassis']
        self.chassis = chassis_t(settings['chassis_settings'])

        server_settings = settings['server_settings']
        self.server = packetcomms.Server(port = server_settings['port'])
        self.server_thread = threading.Thread(target = self.server.loop)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.logger.info("Server loop running in: '%s'", \
                self.server_thread.name)

        self.task = WaypointTask()
        self.sensors = []

    def sense(self, time_now):
        readings = {
            'heading': self.chassis.heading(),
            'position': self.chassis.position(),
        }

        self.logger.debug("Sense: x:%f y:%f theta:%f",
                readings['position'][0], readings['position'][1],
                readings['heading'])

        return readings

    def plan(self, readings):
        # Default states:
        actions = {
            #'left_wheel': (self.left_wheel.set_speed, 0.0),
            #'right_wheel': (self.right_wheel.set_speed, 0.0),
        }

        # Task planning. Should not depend on any previous state
        if self.task:
            actions = self.task.plan(readings)
            #actions.update(task_actions)

        # Commands over the wire should override task activities
        #while self.server.have_packet():
        #    msg = self.server.recv()
        #    cmd_actions = self.handle_message(msg)
        #    actions.update(cmd_actions)

        return actions

    # Set the state of the actuators. actions is a dict of tuples of the
    # actions to perform, as returned by 'plan'
    # { 'actuator_name': (function, [arguments])}
    def act(self, actions):
        if not self.chassis.auto:
            print "Mutley! do {}".format(actions)
            if abs(actions['d_theta']) > math.pi / 16:
                speed = None
                if (abs(actions['d_theta']) < math.pi / 6):
                    speed = 0.1
                self.chassis.turn_rad(0, actions['d_theta'])
            elif abs(actions['distance']):
                self.chassis.line(min(actions['distance'] * 0.7, 200))

    # Loop forever, sensing, planning and acting!
    def loop(self):
        next_time = time.time() + self.tau
        while 1:
            try:
                time_now = time.time()
                if (time_now >= next_time):
                    next_time = time_now + self.tau
                    readings = self.sense(time_now)
                    actions = self.plan(readings)
                    self.act(actions)
            except KeyboardInterrupt:
                self.logger.critical("Caught KeyboardInterrupt. Aborting")
                return

