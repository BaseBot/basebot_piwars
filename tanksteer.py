import math
import threading

import wheel

settings = {
    'tau': 0.1,
    'chassis_width': 200.0,
    'wheel_diameter': 69.0,
    'speed_limiter': 0.8,
    'wheel_settings': {
        'left': {
            'bus': ('i2c', 1),
            'addr': 0x41,
            'servo': 0,
            'threshold': 0x60,
            'slots': 60,
            'curves': [((1413, 1470), (-100,  -2)),\
                       ((1471, 1479), (  -1,  1)),\
                       ((1480, 1536), (  2, 100))],
        },
        'right': {
            'bus': ('i2c', 1),
            'addr': 0x40,
            'servo': 1,
            'threshold': 0x60,
            'slots': 60,
            'curves': [((1540, 1480), (-100, -2)),
                       ((1479, 1471), (-1, 1)),
                       ((1471, 1407), (2, 100))],
        },
    },
}

class Tanksteer:
    def __init__(self, settings):
        self.b = settings['chassis_width']
        self.tau = settings['tau']
        self.slots_per_mm = settings['wheel_diameter'] * math.pi / \
                settings['wheel_settings']['left']['slots']

        # Instantiate our wheels
        self.wheels = (wheel.Wheel(settings['wheel_settings']['left'],
                       wheel.Wheel(settings['wheel_settings']['right']))
        self.odometer = (0, 0)
        self.target = (0, 0)
        self.speed = (0, 0)
        self.update((0, 0), (0, 0))

        # Set up speeds
        self.max_speed = settings['speed_limiter'] * \
                min([w.max_speed() for w in self.wheels.values()])
        # Some conservative default
        self.default_speed = 0.5 * self.max_speed

        # Spawn a thread to tick the wheels
        self.tick_thread = threading.Thread(target=self.__loop)
        self.tick_thread.daemon = True
        self.tick_thread.start()

    def __loop():
        next_time = time.time() + self.tau
        while 1:
            time_now = time.time()
            if (time_now >= next_time):
                next_time = time_now + self.tau
                self.tick()
                for i in range(len(self.wheels)):
                    d = self.odometer[i] - self.target[i]
                    if ((self.speed[i] > 0) and (d >= 0)) or \
                            (self.speed[i] < 0) and (d <= 0)):
                        self.stop()
                        break

    def stop(self):
        self.update((0, 0), (0, 0))

    def tick(self):
        self.wheels[0].tick()
        self.wheels[1].tick()
        self.odometer = (self.wheels[0].count, self.wheels[1].count)

    def update(self, speed, distance):
        self.speed = speed
        self.tick()
        self.target = (self.odometer[0] + distance[0],
                       self.odometer[1] + distance[1])

    def mm_to_slots(self, mm):
        return mm * self.slots_per_mm

    def slots_to_mm(self, slots):
        return (1 / self.slots_mm) * slots

    def speed(self, speed):
        if speed == None:
            return self.default_speed
        speed = max(min(1.0, speed), 0.0)
        return self.max_speed * speed

    def turn_deg(self, radius, angle, speed = None):
        self.turn_rad(radius, math.radians(angle), speed = None)

    # Speed should be 0.0 - 1.0
    # Angle +ve = CCW rotation
    # Radius +ve = Centre of rotation to left of chassis
    #  radius  angle   action
    #   +ve     +ve     Forwards, turning left
    #   +ve     -ve     Backwards, turning right
    #   -ve     -ve     Forwards, turning right
    #   -ve     +ve     Backwards, turning left
    def turn_rad(self, radius, angle, speed = None):
        delta_r = self.b / 2.0
        l_distance = self.mm_to_slots((radius - delta_r) * angle)
        r_distance = self.mm_to_slots((radius + delta_r) * angle)

        # v_l = (2r - b)/(2r + b)*v_r
        # v_r = (2r + b)/(2r - b)*v_l
        velocity = math.copysign(self.speed(speed), radius / angle)
        d = 2.0 * radius
        if radius >= 0:
            # Right wheel is fastest.
            # Fix right wheel. Work out left
            v_r = velocity
            v_l = (d - self.b) / (d + self.b) * v_r
        else:
            v_l = velocity
            v_r = (d + self.b) / (d - self.b) * v_l

        self.update((v_l, v_r), (l_distance, r_distance))

    # Speed should be 0 - 1
    # Distance (in mm) sets direction
    def line(self, distance, speed = None):
        v_r = math.copysign(self.speed(speed), distance)
        v_l = v_r
        distance_slots = self.mm_to_slots(distance)
        self.update((v_l, v_r), (distance_slots, distance_slots))


