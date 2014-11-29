# Line following sensor driver via i2c ADC

import logging
import math
import smbus

def compute_centroid(vals):
    if sum(vals) == 0:
        return None
    mid = len(vals) / 2
    torques = [vals[i] * (i - mid) \
            for i in range(len(vals))]
    centroid = float(sum(torques)) / sum(vals)
    return float(centroid) / (len(vals) / 2)

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

class LineSensor():
    def __init__(self, bus, addr, channels = range(5)):
        tag = '%i:0x%02x' % (1, addr)
        self.logger = logging.getLogger('%s.%s' % \
                (self.__class__.__name__, tag))
        self.bus = bus
        self.addr = addr
        self.channels = channels
        # Number of taps for the moving average filter
        self.n_tap_ma = 100
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

    def threshold(self, vals):
        mu = mean(vals)
        if self.i < self.n_tap_ma:
            self.means.append(mu)
            self.sigma_mu = 0
            self.mu_mu = mu
        else:
            self.means[self.i % self.n_tap_ma] = mu
            self.mu_mu = mean(self.means)
            self.sigma_mu = std_dev(self.means)
        self.i = self.i + 1

        # If a sensor is higher than the mean of the mean
        # sensor readings by a "reasonable" margin, then
        # consider it black
        threshold = self.mu_mu + max(self.sigma_mu, 5)
        return [ 1 if v > threshold else 0 for v in vals ]

    # Returns:
    # 0.0: On centre
    # -1.0 - +1.0: Off-centre (proportiona)
    # +/-2: Possible 90 degree turn
    # None: Line lost
    def find_line(self):
        vals = self.read()
        self.logger.debug("Raw: %s", str(vals))
        thresholded = self.threshold(vals)
        self.logger.debug("Thresholded: %s", str(thresholded))
        centroid = compute_centroid(thresholded)
        if centroid == None:
            return None
        else:
            half = len(vals) / 2
            if thresholded.count(1) <= half:
                return centroid
            else:
                return math.copysign(half, centroid)

    def sense(self):
        return self.find_line()
