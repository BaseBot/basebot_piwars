# Line following sensor driver via i2c ADC

import logging
import math
import smbus

def compute_centroid(vals):
    if sum(vals) == 0:
        return 0
    mid = len(vals) / 2
    torques = [vals[i] * (i - mid) \
            for i in range(len(vals))]
    centroid = float(sum(torques)) / sum(vals)
    print sum(torques)
    return centroid

class LineSensor():
    def __init__(self, bus, addr, channels = range(5)):
        tag = '%i:0x%02x' % (1, addr)
        self.logger = logging.getLogger('%s.%s' % \
                (self.__class__.__name__, tag))
        self.bus = bus
        self.addr = addr
        self.channels = channels
        self.min_seen = [255] * len(channels)
        self.max_seen = [0] * len(channels)

    # Return a value for each sensor channel
    # Higher values are more black
    # Maximum is 1.0
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

        normalised = []
        for i in range(n_chans):
            self.min_seen[i] = min(vals[i], self.min_seen[i])
            self.max_seen[i] = max(vals[i], self.max_seen[i])
            dyn_range = max(float(self.max_seen[i] - self.min_seen[i]), 1.0)
            normalised.append((vals[i] - self.min_seen[i]) / dyn_range)
        return normalised

    def find_line(self):
        vals = self.read()
        return compute_centroid(vals)

    def sense(self):
        return self.find_line()
