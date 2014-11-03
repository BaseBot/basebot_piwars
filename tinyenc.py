# python bindings for the Attiny i2c quadrature encoder:
# http://github.com/usedbytes/i2c_encoder
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import ctypes
import logging

class TinyEnc:
    __debug = 0
    REG_CNT    = 0x0
    REG_CNTH   = 0x1
    REG_STATUS = 0x2
    STATUS_RST  = (1 << 0)
    STATUS_CAL  = (1 << 1)
    STATUS_CMIE = (1 << 2)
    STATUS_CMIF = (1 << 3)
    STATUS_LED0 = (1 << 4)
    STATUS_LED1 = (1 << 5)
    REG_CMP    = 0x3
    REG_CMPH   = 0x4
    REG_MIN    = 0x5
    REG_MAX    = 0x6
    REG_THRESH = 0x7


    def __init__(self, bus, addr):
        tag = '%i:0x%02x' % (bus, addr)
        self.logger = logging.getLogger('%s.%s' % \
                (self.__class__.__name__, tag))
        self.bus = bus
        self.addr = addr
        self.logger.info("New TinyEnc at %i:0x%2x", bus, addr)

    def __read(self, reg, length = 1):
        vals = self.bus.read_i2c_block_data(self.addr, reg, length)
        self.logger.debug("Read %s: %s", hex(reg), vals)
        if length == 1:
            return vals[0]
        else:
            return vals

    def __write(self, reg, data):
        if isinstance(data, int):
            l = [data]
        elif isinstance(data, list):
            l = data
        else:
            raise TypeError
        self.logger.debug("Write %s: %s", hex(reg), l)
        self.bus.write_i2c_block_data(self.addr, reg, l)

    def __setbits(self, reg, bits):
        tmp = self.__read(reg)
        tmp = tmp | bits
        self.__write(reg, tmp)

    def __clearbits(self, reg, bits):
        tmp = self.__read(reg)
        tmp = tmp & ~bits
        self.__write(reg, tmp)

    def get_count(self):
        vals = self.__read(self.REG_CNT, 2)
        count = ctypes.c_short(vals[0] | (vals[1] << 8))
        return count.value

    def get_thresh(self):
        return self.__read(self.REG_THRESH)

    def set_thresh(self, thresh):
        self.__write(self.REG_THRESH, thresh)

    def get_cmp(self):
        vals = self.__read(self.REG_CMP, 2)
        cmp = ctypes.c_short(vals[0] | (vals[1] << 8))
        return cmp.value

    def set_cmp(self, val):
        vals = [val & 0xFF, (val >> 8) & 0xFF]
        self.__write(self.REG_CMP, vals)

    def reset(self):
        self.__setbits(self.REG_STATUS, self.STATUS_RST)

    def cal(self, enable):
        if (enable):
            self.__setbits(self.REG_STATUS, self.STATUS_CAL)
        else:
            self.__clearbits(self.REG_STATUS, self.STATUS_CAL)

    def get_cal(self):
        return self.__read(self.REG_MIN, 2)

    def set_led(self, setting):
        self.__clearbits(self.REG_STATUS, self.STATUS_LED0 | self.STATUS_LED1)
        self.__setbits(self.REG_STATUS, setting)

    def irq(self, enable):
        if (enable):
            self.__setbits(self.REG_STATUS, self.STATUS_CMIE)
        else:
            self.__clearbits(self.REG_STATUS, self.STATUS_CMIE)

    def handle_irq(self):
        self.__clearbits(self.REG_STATUS, self.STATUS_CMIF)

LED_OFF   = 0
LED_PULSE = TinyEnc.STATUS_LED0
LED_IRQ   = TinyEnc.STATUS_LED1

