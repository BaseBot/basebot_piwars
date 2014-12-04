# Wall sensor using IR reflectance sensors

import logging
import math
import smbus

# No numpy in my image, we can fix that :-)
def mean(a):
    return float(sum(a)) / len(a)

def std_dev(a):
    avg = mean(a)
    s = []
    d_sq = []
    for v in a:
        d_sq.append((v - avg)**2)
    return math.sqrt(mean(d_sq))

class WallSensor():
    def __init__(self, bus, addr, channels = range(5)):
        tag = '%i:0x%02x' % (1, addr)
        self.logger = logging.getLogger('%s.%s' % \
                (self.__class__.__name__, tag))
        self.bus = bus
        self.addr = addr
        self.channels = channels
        # Number of taps for the moving average filter
        self.n_tap_ma = 10
        self.i = 0
        # Previous means for the moving average
        self.means = []
        # Moving average of the mean sensor value
        self.mu_mu = 0

    # Return the raw value for each sensor channel
    def read(self):
        n_chans = len(self.channels)
        vals = range(n_chans)
        # Do a single read which includes all our channels
        first = min(self.channels)
        last = max(self.channels)
        length =  (last - first) + 1
        recv = self.bus.read_i2c_block_data(self.addr, first, length)
        # Pull out the channels we're interested in
        vals = [recv[i - first] for i in self.channels]
        return vals

    def sense(self):
        vals = self.read()
        mu = mean(vals)
        if self.i < self.n_tap_ma:
            self.means.append(mu)
            self.sigma_mu = 0
            self.mu_mu = mu
        else:
            self.means[self.i % self.n_tap_ma] = mu
            self.mu_mu = mean(self.means)
            self.sigma_mu = std_dev(self.means)
        return self.mu_mu

