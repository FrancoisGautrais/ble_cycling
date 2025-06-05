from enum import Enum

from bles.common.timer import Time


class Metric:
    class Type(Enum):
        INSTANT = "instant"
        ACCUMULATION = "accumulation"



    def __init__(self, name, mini, maxi, key=None, type=Type.INSTANT):
        self.name = name
        self.min = mini
        self.maxi = maxi
        self.type = type
        self.key = key or name

    @property
    def is_accumulation(self):
        return self.type == self.Type.ACCUMULATION

    @property
    def is_instant(self):
        return self.type == self.Type.INSTANT


class State:
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"

class Step:

    _type_ = None
    _name_ = None


    def __init__(self):
        self.type = self._type_
        self.name = self._name_
        self._acc_time = 0
        self._start_time = 0
        self.state = State.IDLE

    def on_attach(self):
        pass

    def attach(self):
        self._start_time = Time.time()
        self.state = State.RUNNING
        self.on_attach()

    def on_detach(self):
        pass


    def detach(self):
        self._acc_time += (Time.time() - self._start_time)
        self.state = State.IDLE
        self.on_detach()


    def on_pause(self):
        pass

    def pause(self):
        self._acc_time += (Time.time() - self._start_time)
        self.state = State.PAUSED
        self.on_pause()

    def on_resume(self):
        pass

    def resume(self):
        self._start_time = Time.time()
        self.state = State.RUNNING
        self.on_resume()

    @property
    def time(self):
        if self.state == State.RUNNING:
            return self._acc_time + (Time.time()-self._start_time)
        return self._acc_time



    def update(self, data, ):
        """
        Cette méthode est appelée à chaque nouvelle donnée.

        :param data:
        :return: False -> On continue avec ce step
                True -> Le step est fini on passe au suivant
        """
        return True


class TimedStep(Step):

    def __init__(self, duration, params):
        super().__init__()
        self.duration = duration
        self.params = params

    def update(self, data, ):
        return self.time < self.duration


class SyncStep:

    def __init__(self):
        pass






class Program:

    def __init__(self, steps):
        self.steps = list(steps)
        self._index = None
        self.finisehd = False
        self.state = State.IDLE
        self.current : Step = None


    def attach(self, ):
        if not self.current:
            self._index = 0
            self.current = self.steps[self._index]
        self.current.attach()
        self.state = State.RUNNING


    def pause(self):
        self.current.pause()
        self.state = State.PAUSED

    def resume(self):
        self.current.resume()
        self.state = State.RUNNING

    def detach(self):
        self.current.detach()
        self.state = State.IDLE





