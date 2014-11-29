import math
import random

class LineFollowerTask:
    STATE_FOLLOWING = 0
    STATE_LOST = 1
    def __init__(self):
        self.last_known = None
        self.default_speed = 0.60
        self.last_seen = 0.0
        self.state = self.STATE_FOLLOWING
        self.lost_timer = 0
        self.lost_timeout = 10

    def plan(self, readings):
        if not readings.has_key('LineSensor'):
            return {}
        else:
            reading = readings['LineSensor']
            if reading == None:
                if self.state == self.STATE_FOLLOWING:
                    self.lost_timer = self.lost_timer + 1
                    if (self.lost_timer >= self.lost_timeout):
                        self.state = self.STATE_LOST
                    # Panic a little bit
                    if self.last_seen == 0:
                        # We were going straight, pick a random direction
                        sign = random.choice([-1, 1])
                        reading = math.copysign(2, sign)
                    else:
                        reading = math.copysign(abs(self.last_seen * 2), \
                                self.last_seen)
                else:
                    self.state = self.STATE_LOST
                    # Now we need to go into full-on search mode
                    return { 'd_theta': math.copysign(math.pi / 6, \
                            self.last_seen) }
            else:
                self.last_seen = reading
                self.state = self.STATE_FOLLOWING
            diff = self.default_speed * abs(reading) * 0.8
            if reading <= 0.0:
                left = self.default_speed
                right = self.default_speed - diff
                return { 'manual': (left, right) }
            elif reading > 0.0:
                left = self.default_speed - diff
                right = self.default_speed
                return { 'manual': (left, right) }

