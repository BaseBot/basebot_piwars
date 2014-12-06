# Thin wrapper for blinkyeyes.BlinkyEyes() to integrate with the sense/plan/
# act loop of a classrobot.Robot()
# Copyright Brian Starkey 2014 <stark3y@gmail.com>

import Queue
import threading

import PiWars.blinkyeyes

class EyeManager:
    def __init__(self):
        self.eyes = PiWars.blinkyeyes.BlinkyEyes()
        self.action_queue = Queue.Queue(10)
        self.eyes.moveLids(0.1, 0.1)
        # Spawn a thread because some operations may sleep
        self.action_thread = threading.Thread(target=self.loop)
        self.action_thread.daemon = True
        self.action_thread.start()
        print "Thread running in {}".format(
                self.action_thread)

    def loop(self):
        while True:
            action = self.action_queue.get(True)
            action[0](*action[1])

    # Action is a tuple of a string and a list of arguments
    def do(self, action):
        act = action[0]
        args = action[1]
        try:
            if act == 'look':
                # Look needs [l, r, v]
                self.action_queue.put(
                        (self.eyes.moveEyes, args), False)
            elif act == 'lids':
                # Lids needs [l, r]
                self.action_queue.put(
                        (self.eyes.moveLids, args), False)
            elif act == 'blink':
                # Blink needs []
                self.action_queue.put(
                        (self.eyes.blink, []), False)
            elif act == 'wink':
                # Wink needs [True if right]
                self.action_queue.put(
                        (self.eyes.wink, args), False)
            else:
                pass
        except Queue.Full:
            # Queue full. Oh well!
            pass

    def act(self, actions):
        if actions.has_key('eyes'):
            for tup in actions['eyes']:
                self.do(tup)
