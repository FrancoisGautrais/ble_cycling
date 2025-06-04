import threading
import time


class _Time:

    def __init__(self):
        pass

    def time(self):
        return time.time()

Time = _Time()

class Timer:

    def __init__(self, fct, t=1):
        self._thread = None
        self._timer_thread = None
        self._timer_handler = fct
        self._timer_event = threading.Event()
        self._time = t


    def set_timer_handler(self, fct):
        self._timer_handler = fct


    def start(self):
        if not self._timer_thread:
            self._timer_thread = threading.Thread(target=self._timer)
            self._timer_thread.start()

    def stop(self):
        if self._timer_thread:
            self._timer_event.set()
            self._timer_thread.join()

    def _timer(self):
        last = time.time()

        print(f"timer start {threading.get_ident()}")
        self._timer_event.clear()
        while not self._timer_event.is_set():
            next = last + 1
            delta = next - time.time()
            if delta > 0:
                if self._timer_event.wait(delta):
                    if self._timer_event.is_set():
                        return

            last = time.time()
            if self._timer_handler:
                self._timer_handler()
        print("timer stop")