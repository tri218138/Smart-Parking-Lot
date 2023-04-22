from threading import Thread
from threading import Lock
class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
        args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None # parameter for later return value
        # Override the invoker run() to pass callable object
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)
        # Override value passing
    def join(self, *args):
        Thread.join(self, *args)
        return self._return