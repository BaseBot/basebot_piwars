#!/usr/bin/python

import logging
import math
import smbus
import time
import threading

import packetcomms

class Robot():
    def __init__(self, settings):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Robot init")

        self.tau = settings['tau']

        self.server = packetcomms.Server(port = settings['port'])
        self.server_thread = threading.Thread(target = self.server.loop)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.logger.info("Server loop running in: '%s'", \
                self.server_thread.name)

        self.localiser = None
        self.task = None
        self.sensors = []

    # Read all sensors. Returns dict of sensor readings. The following
    # 'sensors' are guaranteed to exist:
    # {
    #   'heading': heading_in_degrees,
    #   'speed': current_straight_line_speed (mm/s),
    #   'x_pos': cartesian_x_coord (mm),
    #   'y_pos': cartesian_y_coord (mm),
    # }
    # Other sensors may exist depending on the robot...
    def sense(self, time_now):
        readings = {
            'heading': 0.0,
            'speed': 0.0,
            'x_pos': 0.0,
            'y_pos': 0.0,
        }
        # Figure out our world state
        # readings = self.localise(time_now)

        # Figure out everything else
        for s in self.sensors:
            readings[s.name] = s.read(time_now)

        return readings

    # Decide commands for actuators. Must return a dict of tuples:
    # { 'actuator_name': (function, [arguments])}
    # This ensures that every actuator ends up with a single command
    # readings is a ductionary of sensor readings, as returned by
    # 'sense'
    def plan(self, readings):
        # Default states:
        actions = {
            #'left_wheel': (self.left_wheel.set_speed, 0.0),
            #'right_wheel': (self.right_wheel.set_speed, 0.0),
        }

        # Task planning. Should not depend on any previous state
        if self.task:
            task_actions = self.task.plan(self, readings)
            actions.update(task_actions)
            pass

        # Commands over the wire should override task activities
        while self.server.have_packet():
            msg = self.server.recv()
            cmd_actions = self.handle_message(msg)
            actions.update(cmd_actions)

        return actions

    # Set the state of the actuators. actions is a dict of tuples of the
    # actions to perform, as returned by 'plan'
    # { 'actuator_name': (function, [arguments])}
    def act(self, actions):
        for action in actions:
            function = action[0]
            args = action[1]
            function(*args)

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

