
from threading import Thread


class AppThread(Thread):

    def __init__(self):
        super().__init__()
        self.killed = False

    def run(self):
        while not self.killed:
            # TODO: call time.sleep() instead
            pass
    
    def stop(self):
        self.killed = True
