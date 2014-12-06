# Differential Drive chassis with dead-reckoning
# Copyright Brian Starkey 2014 <stark3y@gmail.com>
import logging
import math
import threading
import smbus
import time

import wheel

class Tanksteer:
    # Localiser handles dead-reckoning
    class Localiser:
        def __init__(self, b, odometer):
            self.logger = logging.getLogger(self.__class__.__name__)
            self.logger.setLevel(logging.WARNING)
            self.logger.info("Localiser init")
            self.b = b
            self.reset(odometer)
            self.last_time = time.time()

        def reset(self, odometer):
            self.last = odometer
            # TODO: What direction is "forwards"?
            # This assumes that forwards is along the positive Y
            self.theta = math.pi / 2
            self.pos = (0, 0)

        def clamp_theta(self, theta):
            if (theta > math.pi):
                return theta - (2 * math.pi)
            elif (theta < -math.pi):
                return theta + (2 * math.pi)
            else:
                return theta

        # Calculate a new position and heading based on wheel ticks
        def update(self, odometer):
            distance_moved = (odometer[0] - self.last[0], \
                    odometer[1] - self.last[1])
            s = ''

            # Derivation: http://rossum.sourceforge.net/papers/DiffSteer/
            # TODO: Improve the fuzzyness here
            if (distance_moved[0] == distance_moved[1]):
                    #(0.05 * abs(distance_moved[0] + distance_moved[1]))):
                delta_theta = 0.0
                delta_s = (distance_moved[0] * math.cos(self.theta), \
                           distance_moved[1] * math.sin(self.theta))
                s = 'line'
            else:
                turn_r = (self.b / 2) * \
                         ((distance_moved[1] + distance_moved[0]) / \
                          (distance_moved[1] - distance_moved[0]))
                delta_theta = (distance_moved[1] - distance_moved[0]) / self.b
                delta_x = turn_r * \
                        (math.sin(delta_theta + self.theta) - \
                         math.sin(self.theta))
                delta_y = -turn_r * \
                        (math.cos(delta_theta + self.theta) - \
                         math.cos(self.theta))
                delta_s = (delta_x, delta_y)
                s = 'arc'
            self.last = odometer
            self.pos = (self.pos[0] + delta_s[0], self.pos[1] + delta_s[1])
            self.theta = self.clamp_theta(self.theta + delta_theta)
            self.logger.debug("Update: moved(%s):%f %f pos:%f %f",
                    s, distance_moved[0], distance_moved[1], \
                            self.pos[0], self.pos[1])

    def __init__(self, settings):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Tanksteer init")
        self.b = settings['chassis_width']
        self.tau = settings['tau']
        self.slots_per_mm = settings['wheel_settings']['left']['slots'] / \
                (settings['wheel_diameter'] * math.pi)

        # Instantiate our wheels
        self.wheels = (wheel.Wheel(settings['wheel_settings']['left']),
                       wheel.Wheel(settings['wheel_settings']['right']))
        self.odometer = (0, 0)
        self.target = (0, 0)
        self.cur_speed = (0, 0)
        self.update((0, 0), (0, 0))
        self.localiser = Tanksteer.Localiser(self.b, self.odometer)
        self.auto = False

        # Set up speeds
        self.max_speed = settings['speed_limiter'] * \
                min([w.max_speed() for w in self.wheels])
        self.logger.info("Max speed: {}".format(self.max_speed))
        # Some conservative default
        self.default_speed = 0.5 * self.max_speed
        #self.default_speed = 10

        # Spawn a thread to tick the wheels
        self.tick_thread = threading.Thread(target=self.__loop)
        self.tick_thread.daemon = True
        self.tick_thread.start()

    def __loop(self):
        next_time = time.time() + self.tau
        while 1:
            time_now = time.time()
            if (time_now >= next_time):
                next_time = time_now + self.tau
                self.tick()
                self.localiser.update(self.odometer)
                if self.auto:
                    for i in range(len(self.wheels)):
                        d = self.odometer[i] - self.target[i]
                        # Stop if it looks like we completed our movement
                        if ((self.cur_speed[i] > 0) and (d >= 0)) or \
                                ((self.cur_speed[i] < 0) and (d <= 0)):
                            self.stop()
                            break

    def heading(self):
        return self.localiser.theta

    def position(self):
        return self.localiser.pos

    def stop(self):
        self.update((0, 0), (0, 0))

    def tick(self):
        self.wheels[0].tick()
        self.wheels[1].tick()
        # Verbose logging
        if (self.cur_speed[0] != 0) or (self.cur_speed[1] != 0):
            actual = (self.wheels[0].speed, self.wheels[1].speed)
            error = (self.cur_speed[0] - actual[0], \
                     self.cur_speed[1] - actual[1])
            self.logger.debug("set: (%2.2f, %2.2f) " \
                    "actual: (%2.2f, %2.2f) error: (%2.2f, %2.2f)" % \
                    (self.cur_speed[0], self.cur_speed[1], \
                    actual[0], actual[1], error[0], error[1]))
        self.odometer = (self.slots_to_mm(self.wheels[0].count), \
                self.slots_to_mm(self.wheels[1].count))

    def update(self, speed, distance = (0, 0), auto = False):
        self.cur_speed = speed
        self.wheels[0].set_speed(self.cur_speed[0])
        self.wheels[1].set_speed(self.cur_speed[1])
        self.target = (self.odometer[0] + distance[0],
                       self.odometer[1] + distance[1])
        self.auto = auto
        self.tick()
        self.logger.debug( "Odo: {}".format(self.odometer))
        self.logger.debug( "Distance: {}".format(distance))
        self.logger.debug( "Target: {}".format(self.target))

    def mm_to_slots(self, mm):
        return mm * self.slots_per_mm

    def slots_to_mm(self, slots):
        return (1 / self.slots_per_mm) * slots

    # Return a speed in slots/s given input 0-1.0
    def speed(self, speed):
        if speed == None:
            return self.default_speed
        speed = max(min(1.0, speed), 0.0)
        speed = self.max_speed * speed
        return speed

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
        l_distance = ((radius - delta_r) * angle)
        r_distance = ((radius + delta_r) * angle)

        # v_l = (2r - b)/(2r + b)*v_r
        # v_r = (2r + b)/(2r - b)*v_l
        velocity = math.copysign(self.speed(speed), radius / angle)
        velocity = velocity / 2
        d = 2.0 * radius
        if radius >= 0:
            # Right wheel is fastest.
            # Fix right wheel. Work out left
            v_r = velocity
            v_l = (d - self.b) / (d + self.b) * v_r
        else:
            # Left wheel is fastest.
            # Fix left wheel. Work out right
            v_l = velocity
            v_r = (d + self.b) / (d - self.b) * v_l

        self.update((v_l, v_r), (l_distance, r_distance), True)

    # Speed should be 0 - 1
    # Distance (in mm) sets direction
    def line(self, distance, speed = None):
        if abs(distance) > 1:
            v_r = math.copysign(self.speed(speed), distance)
            v_l = v_r
            self.update((v_l, v_r), (distance, distance), True)


