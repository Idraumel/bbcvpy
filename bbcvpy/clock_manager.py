import time

class ClockManager:
    clock = None

    def __init__(self):
        pass

    def start_clock(self):
        if self.clock:
            raise Exception("There is already an active clock")
        self.clock = time.time()
    
    def stop_clock(self):
        if not self.clock: raise Exception("There is no active clock")
        exec_time = time.time() - self.clock
        self.clock = None
        return exec_time