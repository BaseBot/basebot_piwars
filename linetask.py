
class LineFollowerTask:
    def __init__(self):
        self.last_known = None
        self.default_speed = 0.25
        self.max_delta = 0.08

    def plan(self, readings):
        if not readings.has_key('LineSensor'):
            return {}
        else:
            reading = readings['LineSensor']
            diff = self.max_delta * abs(readings['LineSensor'])
            if reading < 0.0:
                left = self.default_speed + diff
                right = -(self.default_speed / 2) if reading <= 1.5 \
                        else self.default_speed - diff
                return { 'manual': (left, right) }
            elif reading > 0.0:
                left = -(self.default_speed / 2) if reading >= 1.5 \
                        else  self.default_speed - diff
                right = self.default_speed + diff
                return { 'manual': (left, right) }
            else:
                return { 'manual': (self.default_speed, self.default_speed) }

