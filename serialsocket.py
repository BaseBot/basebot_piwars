#/usr/bin/python
# Reads data from the serial port and forwards it on to a packetcomms.Server
# Hopefully the data is well-formed packetcomms.Packet()s!
# Copyright Brian Starkey 2014 <stark3y@gmail.com>

import logging
import serial
import socket

class SerialSocket:
    def __init__(self, settings):
        self.tag = "%s.%s" % (self.__class__.__name__, \
                settings['serial_settings']['port'])
        self.logger = logging.getLogger(self.tag)
        self.server = (settings['server_settings']['host'],
                settings['server_settings']['port'])
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.server)

        self.ser = serial.Serial()
        self.ser.port = settings['serial_settings']['port']
        self.ser.baudrate = settings['serial_settings']['baud']
        self.ser.timeout = 60
        self.ser.open()
        self.logger.info("SerialSocket init success")

    def reconnect(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.server)
        self.logger.info("Reconnect success.")

    def loop(self):
        while True:
            s = self.ser.read(1)
            if self.ser.inWaiting():
                s = s + self.ser.read(self.ser.inWaiting())
            if len(s):
                try:
                    self.sock.sendall(s)
                except:
                    self.logger.error("Caught socket exception. Reconnect...")
                    self.reconnect()
