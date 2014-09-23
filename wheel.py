# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import tinyenc
import servo
import time

class Wheel:
    class Controller:
        def __init__(self, settings):
            self.setpoint = 0
            self.line_segs = []
            max_kc = 0
            min_kc = 0
            for l in settings["curves"]:
                seg = {}
                seg['min_x'] = float(l[0][0])
                seg['max_x'] = float(l[0][1])
                seg['mid_x'] = (seg['min_x'] + seg['max_x']) / 2.0
                seg['min_y'] = float(l[1][0])
                seg['max_y'] = float(l[1][1])
                seg['mid_y'] = (seg['min_y'] + seg['max_y']) / 2.0
                seg['dydx'] = (seg['max_y'] - seg['min_y']) / \
                        (seg['max_x'] - seg['min_x'])
                try:
                    seg['kc'] = 0.5 / seg['dydx']
                    #seg['ki'] = seg['kc'] * 0.5
                except ZeroDivisionError:
                    self.prev_out = seg['mid_x']
                    seg['kc'] = 0.0
                    #seg['ki'] = 1.0
                self.line_segs.append(seg)
                max_kc = max(max_kc, seg['kc'])
                min_kc = min(min_kc, seg['kc'])
                #print str(seg)
            if abs(min_kc) > max_kc:
                max_kc = min_kc
            self.ki = max_kc * 0.1
            self.iterm = 0
            self.sum_T = 0
            self.set_point(0.0)
            #print "KI: %f" % self.ki
            pass

        def set_point(self, setpoint):
            self.setpoint = setpoint
            smallest_y = 0
            largest_y = 0
            smallest_s = None
            largest_s = None
            for s in self.line_segs:
                if (int(s['max_y']) == int(s['min_y']) == int(setpoint)):
                    self.seg = s
                    return
                elif (s['max_y'] > setpoint > s['min_y']):
                    self.seg = s
                    return
                else:
                    smallest_y = min(smallest_y, s['min_y'])
                    if (smallest_y == s['min_y']):
                        smallest_s = s
                    largest_y = max(largest_y, s['max_y'])
                    if (largest_y == s['max_y']):
                        largest_s = s
            if (setpoint <= smallest_y):
                self.seg = smallest_s
            if (setpoint >= largest_y):
                self.seg = largest_s
            return

        def calculate(self, pv, tick_T):
            since_last = self.sum_T + tick_T
            if ((self.setpoint < 1) or (since_last >= (1 / self.setpoint))):
                self.sum_T = 0
                err = self.setpoint - pv
                self.iterm = self.iterm * 0.5
                self.iterm = (self.iterm) + (self.ki * err * since_last)
                #print "iterm: %f" % self.iterm
                out = self.prev_out + (self.seg['kc'] * err)
                if (0.01 >= self.seg['kc'] > -0.01):
                    out = self.seg['mid_x']
                out = out + self.iterm
                if (self.ki > 0.0):
                    out = max(min(self.seg['max_x'] + 10, out), self.seg['min_x'] - 10)
                else:
                    out = min(max(self.seg['max_x'] - 10, out), self.seg['min_x'] + 10)
                out = int(out)
                self.prev_out = out
                return out
            else:
                self.sum_T = since_last
                return self.prev_out

    def __init__(self, settings):
        self.settings = settings
        self.servo = servo.Servo(settings['servo'])
        self.encoder = tinyenc.TinyEnc(settings['i2c_bus'], settings['addr'])
        self.encoder.set_thresh(settings['threshold'])
        self.encoder.reset()
        self.encoder.set_led(tinyenc.LED_PULSE)
        self.old_count = 0
        self.speed = 0
        self.servo_us = 0
        self.controller = Wheel.Controller(settings)
        self.set_speed(0)
        self.last_time = time.time()
        self.servo_us = self.controller.calculate(self.speed, 0)

    def __str__(self):
        #s = "Speed: %ideg/s Setpoint: %ideg/s Servo: %ius Pos: %i" % (\
                #self.speed, self.controller.setpoint, self.servo_us, \
                #self.old_count)
        s = "%i,%i,%i" % (self.servo_us, self.speed, self.controller.setpoint)
        return s

    def set_speed(self, speed):
        self.controller.set_point(speed)
        #self.servo_us = speed
        #self.servo.set_us(speed)

    def reset(self):
        self.old_count = 0
        self.encoder.reset()

    def get_position(self):
        return self.encoder.get_count()

    def tick(self):
        now = time.time()
        T = now - self.last_time
        count = self.get_position()
        d_count = count - self.old_count
        self.speed = d_count / T
        self.servo_us = self.controller.calculate(self.speed, T)
        self.servo.set_us(self.servo_us)
        self.last_time = now
        self.old_count = count
