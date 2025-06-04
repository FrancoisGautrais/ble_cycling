import random
import threading
import time
from abc import abstractmethod
from asyncio import Queue

from bles.ble.base import BaseBleClient, EventMixin, Exit, register_ble_client, Message
from bles.ble import features
from bles.ble.fitness import SetResistance, SetPower, SetSimulationParam, CyclingData
from bles.ble.heart import HRSState




class DebugBleClient(BaseBleClient, EventMixin):
    _debug_ = True
    _connection_time_ = 0.2


    def __init__(self, timer=None):
        BaseBleClient.__init__(self)
        EventMixin.__init__(self)
        self.simu = None
        self.timer = timer
        self._connected = False

    def __enter__(self):
        self._start_service()
        self._connected = True
        self._connection_event.set()
        if self._on_connect:
            self._on_connect(self)

        return self


    @property
    def is_connected(self):
        return self._connected

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_services()
        self._connected = False

    def set_debug_simulator(self, simu):
        self.simu = simu

    def _thread_main(self, iteration=None):
        self.do_continue = True
        timer = 1
        last_timer = time.time()
        while self.do_continue:
            with self:
                while self.do_continue:
                    while not self.queue.empty():
                        next = self.queue.get()
                        assert isinstance(next, Message)
                        if isinstance(next, Exit):
                            self.do_continue = False
                            return
                        else:
                            self._on_message(next)

                    sleep_time = 0
                    if timer is not None:
                        next = timer + last_timer
                        sleep_time = next - time.time()

                    if sleep_time > 0:
                        if self._changed.wait(sleep_time):
                            self._changed.clear()

                    if timer is not None:
                        self._on_timer()
                        last_timer = time.time()

    def stop(self):
        self._add_event(Exit())


    def _start_service(self):
        if self._connection_time_:
            time.sleep(self._connection_time_)

    def _stop_services(self):
        pass

    def _on_message(self, message):
        field = message._field_.lower()

        fct = getattr(self, f"on_{field}", None)
        if fct is None:
            raise NotImplementedError(f"Impossible de trouver la callback ('on_{field}') pour {message}")

        fct(message)

    def _on_timer(self):
        pass


@register_ble_client
class FitnessClientDebug(DebugBleClient):
    _data_class_ = CyclingData
    _feature_ = features.cycling

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._nominal_power = 0
        self.power_range = [0, 3000]
        self.resistance_range = [0, 100]

    def set_resistance(self, x):
        self._add_event(SetResistance(x))

    def set_power(self, x):
        self._add_event(SetPower(x))

    def set_simulation_param(self, wind, grad, crr, cw):
        self._add_event(SetSimulationParam((wind, grad, crr, cw)))

    def _on_message(self, next):
        v  = next.value
        if isinstance(next, SetPower):
            self._nominal_power = v

    def _on_timer(self):
        effective_power = max(self._nominal_power + random.randint(-10, 10),0)

        speed = effective_power * 0.1
        self.simu.step(effective_power)
        self._set_data(
            speed=speed,
            cadence = random.randint(60,100),
            distance = 0,
            resistance = 0,
            power = effective_power
        )



@register_ble_client
class HRClientDebug(DebugBleClient):
    _data_class_ = HRSState
    _feature_ = features.heart_rate


    def _on_message(self, next):
        pass

    def _on_timer(self):
        self._set_data(
            bpm=self.simu.last_bpm
        )

