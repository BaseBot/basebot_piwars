import logging
import math
import random

class LineFollowerTask:
    STATE_FOLLOWING = 0
    STATE_LOST = 1
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.last_known = None
        self.default_speed = 0.60
        self.last_seen = 0.0
        self.state = self.STATE_FOLLOWING
        self.lost_timer = 0
        self.lost_timeout = 8
        self.lost_step = 0
        self.lost_turn = math.pi / 2

    def plan(self, readings):
        if not readings.has_key('LineSensor'):
            return {}
        else:
            reading = readings['LineSensor']
            if reading == None:
                if self.state == self.STATE_FOLLOWING:
                    self.lost_timer = self.lost_timer + 1
                    # We're properly lost
                    if (self.lost_timer >= self.lost_timeout):
                        self.state = self.STATE_LOST
                        self.lost_step = 0

                    # Only panic a little bit
                    if self.last_seen == 0:
                        # We were going straight, pick a random direction
                        sign = random.choice([-1, 1])
                        reading = math.copysign(2, sign)
                    else:
                        reading = math.copysign(abs(self.last_seen * 2), \
                                self.last_seen)
                else:
                    # Now we need to go into full-on search mode
                    if readings['auto']:
                        # Wait until we finished the last bit
                        return {}

                    actions = {}
                    if self.lost_step == 0:
                        # Turn
                        self.logger.debug(\
                                "Lost stage {}!".format(self.lost_step))
                        actions = { 'd_theta': \
                                math.copysign(self.lost_turn, \
                                self.last_seen) }
                    elif self.lost_step == 1:
                        # Line
                        self.logger.debug(\
                                "Lost stage {}!".format(self.lost_step))
                        actions = { 'distance': 200 }
                    elif self.lost_step == 2:
                        # Turn
                        self.logger.debug(\
                                "Lost stage {}!".format(self.lost_step))
                        actions = { 'd_theta': \
                                math.copysign(self.lost_turn, \
                                self.last_seen) }
                    elif self.lost_step == 3:
                        # Line
                        self.logger.debug(\
                                "Lost stage {}!".format(self.lost_step))
                        actions = { 'distance': 250 }
                    elif self.lost_step == 4:
                        # Turn back
                        self.logger.debug(\
                                "Lost stage {}!".format(self.lost_step))
                        actions = { 'd_theta': \
                                -math.copysign(self.lost_turn, \
                                self.last_seen) }
                    elif self.lost_step == 5:
                        # Long line
                        self.logger.debug(\
                                "Lost stage {}!".format(self.lost_step))
                        actions = { 'distance': 250 }
                    elif self.lost_step == 6:
                        # Turn back
                        self.logger.debug(\
                                "Lost stage {}!".format(self.lost_step))
                        actions = { 'd_theta': \
                                -math.copysign(self.lost_turn, \
                                self.last_seen) }
                    elif self.lost_step == 7:
                        # Long line
                        self.logger.debug(\
                                "Lost stage {}!".format(self.lost_step))
                        actions = { 'distance': 250 }
                    elif self.lost_step == 8:
                        # Arc one way
                        self.logger.debug(\
                            "Lost stage {}!".format(self.lost_step))
                        actions = { 'arc': { 'radius': 300, \
                                'angle': 2 * math.pi } }
                    elif self.lost_step == 9:
                        # Arc the other
                        self.logger.debug(\
                                "Lost stage {}!".format(self.lost_step))
                        actions = { 'arc': { 'radius': 300, \
                                'angle': -2 * math.pi } }
                    else:
                        raise RuntimeError("I got lost :-(")
                    self.lost_step = self.lost_step + 1
                    return actions
            else:
                self.last_seen = reading
                self.state = self.STATE_FOLLOWING
                self.lost_timer = 0
            diff = self.default_speed * abs(reading) * 0.8
            if reading <= 0.0:
                left = self.default_speed
                right = self.default_speed - diff
                return { 'manual': (left, right) }
            elif reading > 0.0:
                left = self.default_speed - diff
                right = self.default_speed
                return { 'manual': (left, right) }

