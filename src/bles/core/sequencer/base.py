import copy
import json
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from bles.core.ble import get_ble_client, features
from bles.common.config import SequencerConfig, config
from bles.core.controller.base import get_controller, list_controller, BaseController
from bles.core.driver.base import BaseDriver
from bles.core.simulator.base_simulator import PowerSimulator, show
from bles.app.stats.base import Stat



class BaseSequencer(BaseDriver):
    STATUS_IDLE = "IDLE"
    STATUS_CONNECTING = "CONNECTING"
    STATUS_RUNNING = "RUNNING"
    STATUS_PAUSED = "PAUSED"

    def __init__(self, config=None, on_data_cb=None):
        self._devices = {}
        self._ble_clients = {}
        self._controllers = {}
        self._thread = None
        self._stopped = threading.Event()
        self._lock = threading.Lock()
        self.config : SequencerConfig = config
        self.status = self.STATUS_IDLE
        self.data_lock = threading.Lock()

        self._current_controller = None
        self._simulator = None
        self._handlers = {}
        self._on_data_handler = on_data_cb
        self._last_notify = 0
        self.data = {}
        self.ready = False

    def set_on_data_handler(self, cb):
        self._on_data_handler = cb

    def use_simulator(self, simu):
        self._simulator = simu

    def set_config(self, config):
        self.config = config

    @property
    def debug(self):
        return self._simulator is not None


    def use_controller(self, name):
        self._current_controller = self._controllers[name]
        return self._current_controller

    def get_controller(self):
        return self._current_controller

    def get_controller_name(self):
        return self._current_controller._name_ if self._current_controller else None

    def _connect_devices(self):
        debug = self.debug
        if debug:

            for feature, desc in self.config.ble_clients.items():
                cls = get_ble_client(feature, True)
                client = cls(**desc["params"])
                client.add_handler(self._on_data_wrapper)
                client.on_disconnect(self._on_disconnect)
                client.on_connect(self._on_connect)

                self._ble_clients[feature] = client
                client.set_debug_simulator(self._simulator)
        else:

            for name, desc in self.config.devices.items():
                self._devices[name] = desc

            for feature, desc in self.config.ble_clients.items():
                cls = get_ble_client(feature, False)
                address = self._devices[desc["device"]]
                client = cls(address, **desc["params"])
                client.add_handler(self._on_data_wrapper)
                client.on_disconnect(self._on_disconnect)
                client.on_connect(self._on_connect)

                self._ble_clients[feature] = client


        for name, ctrl in self.config.controllers.items():
            cls = get_controller(name)
            for x in cls._requires_:
                if x not in self._ble_clients:
                    raise TypeError(f"Aucun client gérant la feature '{x}' n'est disponible")

        for name, ble in self._ble_clients.items():
            print(f"Connecting {name} ...")
            ble.run_thread()
            #
            # for name, ble in self._ble_clients.items():
            if not ble.wait_for_connection(None):
                raise TimeoutError(f"Name={name}")
            print(f"{name}  connected !...")

        for name, ctrl in self.config.controllers.items():
            cls = get_controller(name)
            controller = cls(self, **ctrl["params"])
            self._controllers[name] = controller



    def get_client(self, feature):
        return self._ble_clients[feature]



    def add_handler(self, fct, feature=None):
        if feature is None or isinstance(feature, str):
            feature = [feature]

        for f in feature:
            self._handlers[f] = fct

    def _store_data(self, feature, data):
        with self.data_lock:
            self.data[feature] = copy.copy(data)

    def _on_data_wrapper(self, feature, data):
        self._store_data(feature, data)
        self._on_data(feature, data)
        if feature in self._handlers:
            self._handlers[feature](feature, data)
        if None in self._handlers:
            self._handlers[None](feature, data)

    def _on_data(self, feature, data):
        if self._on_data_handler:
            self._on_data_handler(feature, self.data)

    def _on_connect(self, client):
        pass

    def _on_disconnect(self, client):
        pass

    def start(self):
        print("----------------", self._thread)
        assert not self._thread
        self._thread = threading.Thread(target=self.run, args=())
        self._thread.start()



    def pause(self):
        with self._lock:
            if self.status == self.STATUS_RUNNING:
                self.status = self.STATUS_PAUSED

    def resume(self):
        with self._lock:
            if self.status == self.STATUS_PAUSED:
                self.status = self.STATUS_RUNNING


    def stop(self):

        print(f"Closing devices")
        for feature, ble in self._ble_clients.items():
            ble.stop()

        print(f"Joining devices")
        for feature, ble in self._ble_clients.items():
            ble.join()

        self._ble_clients = {}


        for name, ctrl in self._controllers.items():
            ctrl.disconnect()
        self._controllers = {}

        with self._lock:
            if self.status in (self.STATUS_PAUSED, self.STATUS_RUNNING):
                self._stopped.set()
                self.status = self.STATUS_IDLE

        if self._thread:
            self.join()


    def set_prop(self, name, value):
        if self._current_controller is None:
            raise ValueError(f"Aucun controller n'es selectionné")
        return self._current_controller.set_prop(name, value)


    def set_prop(self, name, value):
        if self._current_controller is None:
            raise ValueError(f"Aucun controller n'es selectionné")
        return self._current_controller.set_prop(name, value)


    def set_prop(self, name, value):
        if self._current_controller is None:
            raise ValueError(f"Aucun controller n'es selectionné")
        return self._current_controller.set_prop(name, value)


    def ctrl_set_prop(self, name, value):
        if self._current_controller is None:
            raise ValueError(f"Aucun controller n'es selectionné")
        return self._current_controller.set_prop(name, value)

    def ctrl_get_prop(self, name):
        if self._current_controller is None:
            raise ValueError(f"Aucun controller n'es selectionné")
        return self._current_controllerget_prop(name)

    def ctrl_call_function(self, name, data):
        if self._current_controller is None:
            raise ValueError(f"Aucun controller n'es selectionné")
        return self._current_controller.call_function(name, data)

    def run(self):
        self.status = self.STATUS_CONNECTING
        self._connect_devices()
        self.ready = True
        self.status = self.STATUS_RUNNING
        while not self._stopped.is_set():
            self._stopped.wait()
        self.ready = False


    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.join()
        else:
            self.stop()

    def join(self):
        if self._thread:
            self._thread.join()
            self._thread = None






class ControllableSequencer(BaseSequencer):

    def _on_connect(self, client):
        print(f"Connected to {client} ! ")


    def _on_disconnect(self, client):
        print(f"Disonnected to {client} ! ")

    def get_status(self):
        return {
            "instant_data": self.data,
            "devices": {
                k: v.get_status() for k, v in self._ble_clients.items()
            },
            "controllers" : {
                k: v.get_status() for k, v in self._controllers.items()
            },
            "status": self.status,
            "current_controller" : self._current_controller and self._current_controller._name_
        }




def set_power(self, power, duration):
    print(f"Setting power to {power} for {duration} s")
    ctrl = self.use_controller("power")
    ctrl.set_prop("power", power)
    time.sleep(duration)


def debug():
    config = SequencerConfig()
    all_features = [features.cycling, features.heart_rate]

    for x in all_features:
        config.add_ble_client(x, x, timer=1)

    for x in list_controller():
        config.add_controller(x)


    base = ControllableSequencer(config)

    base.use_simulator(PowerSimulator(init_freq=80))

    api = ServerInterface()
    api.set_sequencer(base)
    api.run_server(True)


    data = {
        "x" : [],
        "power" : [],
        "fc" : []
    }

    def _print(*args, self=base, d=data):
        d["x"].append(len(d["x"]))
        cycling = self.data.get("cycling")
        hr = self.data.get("heart_rate")
        d["power"].append(cycling.power if cycling else 0)
        d["fc"].append(hr.bpm if hr else 0)
        print(f"recieved {self.data}")

    base.add_handler(_print, "heart_rate")

    # with base:
    #     print("Ready  1 !")
    #
    #     for x in [100,150,200,150,220]:
    #         set_power(base, x, 10)
    #
    # show(data["x"], data["power"], data["fc"] )

def real():

    config = SequencerConfig()

    config.add_device(features.cycling, 'FB:6B:21:56:45:A7')
    config.add_device(features.heart_rate, 'D2:60:F3:44:A7:07')


    all_features = [features.cycling, features.heart_rate]

    for x in all_features:
        config.add_ble_client(x, x)

    for x in list_controller():
        config.add_controller(x)


    base = ControllableSequencer(config)


    def _print(*args, self=base):
        print(f"DATA={self.data}")

    base.add_handler(_print, features.heart_rate)
    base.add_handler(_print, features.cycling)

    with base:
        print("Ready  1 !")

        for x in [50,100,150,200,150,220]:
            set_power(base, x, 5)

        print("closing")
        base.stop()



if __name__ == '__main__':
    real()
