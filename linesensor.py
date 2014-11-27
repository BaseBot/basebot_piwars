# Line following sensor driver via i2c ADC

import logging
import smbus

def compute_centroid(vals):
    if sum(vals) == 0:
        return 0
    mid = len(vals) / 2
    torques = [vals[i] * (i - mid) for i in range(len(vals))]
    total = sum(torques)
    centroid = float(total) / sum(vals)
    return centroid

class LineSensor():
    def __init__(self, bus, addr, channels = range(5)):
        tag = '%i:0x%02x' % (1, addr)
        self.logger = logging.getLogger('%s.%s' % \
                (self.__class__.__name__, tag))
        self.bus = bus
        self.addr = addr
        self.channels = channels

    # Return a value for each sensor channel
    # Higher values are more black
    def read(self):
        vals = range(len(self.channels))
        # Do a single read which includes all our channels
        first = min(self.channels)
        last = max(self.channels)
        length =  (last - first) + 1
        recv = self.bus.read_i2c_block_data(self.addr, first, length)
        # Pull out the channels we're interested in
        vals = [recv[i - first] for i in self.channels]
        return vals

    def find_line(self):
        vals = self.read()
        return compute_centroid(vals)
