import threading

class CancellableTimer(threading.Timer):
    def __init__(self, interval, function, args=None, kwargs=None):
        super().__init__(interval, function, args=args, kwargs=kwargs)
        self._is_canceled = threading.Event()

    def cancel(self):
        self._is_canceled.set()
        super().cancel()

    def is_canceled(self):
        return self._is_canceled.is_set()