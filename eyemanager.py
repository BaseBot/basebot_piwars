import Queue
import threading

import PiWars.blinkyeyes

class EyeManager:
    def __init__(self):
        self.eyes = PiWars.blinkyeyes.BlinkyEyes()
        self.action_queue = Queue.Queue(10)
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
        print "{}".format(action)
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
                print "No such action {}".format(act)
        except Queue.Full:
            # Queue full. Oh well!
            pass
