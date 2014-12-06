#!/usr/bin/python2
# Very very basic uevent joystick driver. Don't know if it works with
# anything other than xpad. Everything in here is based of a quick scan of
# /dev/input/js0 with a hex editor.
# Copyright Brian Starkey 2014 <stark3y@gmail.com>
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import struct
import collections
import Queue
import os
import fcntl
import threading

Event = collections.namedtuple('Event', ['ts', 'val', 'evtype', 'axis'])


TYPE_BUTTON = 1
TYPE_AXIS = 2
TYPE_INIT = 0x80

class Joystick:
    def __init__(self, path = '/dev/input/js0', enable_by_default = True):
        self.fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        self.evqueue = Queue.Queue()
        self.buttons = {}
        self.axes = {}
        format_str = '<IhBB'
        self.struct = struct.Struct(format_str)
        # Seems like the first thing that happens is each axis gets
        # enumerated with an event with "type" having the top bit set
        # We will read all of these, using non-blocking IO to tell when it's
        # done (the reads will start to fail)
        try:
            while 1:
                s = os.read(self.fd, self.struct.size)
                ev = Event(*self.struct.unpack(s))
                if (ev.evtype == (TYPE_INIT | TYPE_BUTTON)):
                    self.buttons[ev.axis] = enable_by_default
                elif (ev.evtype == (TYPE_INIT | TYPE_AXIS)):
                    self.axes[ev.axis] = enable_by_default
                else:
                    break
        except OSError:
            pass
        # Put the file in blocking mode now
        flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        flags = flags & ~os.O_NONBLOCK
        fcntl.fcntl(self.fd, fcntl.F_SETFL, flags)
        # Use a file object because it's nicer :-)
        self.f = os.fdopen(self.fd, 'r')
        # Spawn a thread to pump for events
        self.poll_thread = threading.Thread(target=self.__loop)
        self.poll_thread.daemon = True
        self.poll_thread.start()
        print "Initialised Joystick at '%s'" % path
        print "Enabled Buttons: %s" % str(self.buttons)
        print "Enabled Axes: %s" % str(self.axes)

    # Enable a button or axis
    def enable(self, evtype, axis, enable):
        if (evtype == TYPE_BUTTON):
            self.buttons[axis] = enable
        elif (evtype == TYPE_AXIS):
            self.axes[axis] = enable
        else:
            raise ValueError

    def get(self):
        return self.evqueue.get()

    def have_events(self):
        return not self.evqueue.empty()

    def __loop(self):
        while 1:
            s = self.f.read(self.struct.size)
            ev = Event(*self.struct.unpack(s))
            if (ev.evtype == (TYPE_BUTTON)):
                if self.buttons[ev.axis]:
                    self.evqueue.put(ev)
            elif (ev.evtype == (TYPE_AXIS)):
                if self.axes[ev.axis]:
                    self.evqueue.put(ev)
            else:
                raise ValueError
