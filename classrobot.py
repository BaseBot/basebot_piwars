#!/usr/bin/python

import logging
import math
import Queue
import smbus
import time
import threading

import packetcomms

class Robot():
    def __init__(self, settings):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Robot init")

        self.tau = settings['tau']

        chassis_t = settings['platform']['chassis']
        self.chassis = chassis_t(settings['chassis_settings'])

        server_settings = settings['server_settings']
        self.server = packetcomms.Server(server_address =
                server_settings['host'],\
                port = server_settings['port'])
        self.server_thread = threading.Thread(target = self.server.loop)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.logger.info("Server loop running in: '%s'", \
                self.server_thread.name)

        self.task = None
        self.old_task = None
        self.sensors = settings['sensors']

    def sense(self, time_now):
        readings = {
            'heading': self.chassis.heading(),
            'position': self.chassis.position(),
            'odometer': self.chassis.odometer,
            'auto': self.chassis.auto,
        }

        self.logger.debug("Sense: x:%f y:%f theta:%f",
                readings['position'][0], readings['position'][1],
                readings['heading'])
        for (name, sensor) in self.sensors.iteritems():
            readings[name] = sensor.sense()

        return readings

    def handle_message(self, message):
        packet = message[1]
        if packet.type() == 'tcmd':
            return { 'manual': (packet.body.left, packet.body.right) }
        elif packet.type() == 'text':
            if packet.body.data == 'resume':
                return { 'resume': True }
        else:
            return {}

    def plan(self, readings):
        actions = {
        }

        # Task planning. Should not depend on any previous state
        if self.task:
            task_actions = self.task.plan(readings)
            actions.update(task_actions)

        # Commands over the wire should override task activities
        while self.server.have_packet():
            msg = self.server.recv()
            cmd_actions = self.handle_message(msg)
            if cmd_actions.has_key('manual'):
                if self.task:
                    self.old_task = self.task
                    self.task = None
                actions['manual'] = cmd_actions['manual']
            if cmd_actions.has_key('resume'):
                self.task = self.old_task

        return actions

    def act(self, actions):
        # Manual should override everything!
        if actions.has_key('manual'):
            manual = actions['manual']
            left = math.copysign(self.chassis.speed(abs(manual[0])),\
                    manual[0])
            right = math.copysign(self.chassis.speed(abs(manual[1])),\
                    manual[1])
            speeds = (left, right)
            self.chassis.update(speeds)
        # Otherwise do auto commands if we aren't already busy
        elif not self.chassis.auto:
            self.logger.debug("Auto: {}".format(actions))
            if actions.has_key('d_theta') and \
                    abs(actions['d_theta']) > math.pi / 16:
                speed = None
                if (abs(actions['d_theta']) < math.pi / 16):
                    speed = 0.1
                self.chassis.turn_rad(0, actions['d_theta'])
            elif actions.has_key('distance') and abs(actions['distance']):
                self.chassis.line(min(actions['distance'] * 0.7, 400))
            elif actions.has_key('arc'):
                arc = actions['arc']
                self.chassis.turn_rad(arc['radius'], arc['angle'])

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
            except:
                self.chassis.stop()
                raise

