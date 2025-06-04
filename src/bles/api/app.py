import inspect
import json
import threading
import time
from queue import Queue

from fastapi import Body, Request
from pydantic import BaseModel

from bles.api.server import HttpBaseServer, Get, Post, Put, Delete, JsonBody
from bles.ble import features
from bles.controller import list_controller, get_controller
from bles.controller.base import ControllerFunction
from bles.sequencer.base import ControllableSequencer, SequencerConfig
from bles.simulator.base_simulator import PowerSimulator


class FunctionCall(BaseModel):
    name: str
    arguments: dict = None



class ServerInterface(HttpBaseServer):

    def __init__(self, host=None, port=None, sequencer=None):
        super().__init__(host, port)
        self.sequencer : ControllableSequencer = sequencer
        if self.sequencer:
            self.sequencer.set_on_data_handler(self._on_data)
        self.queue = Queue(maxsize=2048)
        self._lock = threading.Lock()

    @property
    def controller(self):
        return self.sequencer.get_controller()

    @property
    def controller_name(self):
        ctrl = self.controller
        return ctrl and ctrl._name_

    def set_sequencer(self, seq):
        if self.sequencer:
            self.sequencer.set_on_data_handler(None)
        self.sequencer = seq
        self.sequencer.set_on_data_handler(self._on_data)


    @Get("/sequencer/status")
    def _get_status(self):
        return self.sequencer.get_status()


    @Get("/exit")
    def _exit(self):
        self._stop()
        self.server_stop()

    @Get("/sequencer/start")
    def _start(self):
        self.sequencer.start()

    @Get("/sequencer/stop")
    def _stop(self):
        self.sequencer.stop()




    @Get("/sequencer/controllers")
    def _get_controllers(self):
        if self.sequencer.status in (ControllableSequencer.STATUS_RUNNING, ControllableSequencer.STATUS_PAUSED):
            return [
                v.get_description(v)
                for v in self.sequencer._controllers.values()
            ]
        else:
            return [
                get_controller(v["name"]).get_description()
                for v in self.sequencer.config.controllers.values()
            ]


    def _assert_started(self):
        if self.sequencer.status not in (ControllableSequencer.STATUS_RUNNING, ControllableSequencer.STATUS_PAUSED):
            RuntimeError("not started")

    @Get("/sequencer/controllers/{controller}")
    def _get_controllers_c(self, controller: str):
        if self.sequencer.status in (ControllableSequencer.STATUS_RUNNING, ControllableSequencer.STATUS_PAUSED):
            x = self.sequencer._controllers[controller]
            return x.get_description(x)
        else:
            return self.sequencer.config.controllers[controller].get_description()

    @Get("/sequencer/controllers/{controller}/use")
    def _get_controllers_use(self, controller: str):
        self._assert_started()
        self.sequencer.use_controller(controller)

    @Get("/sequencer/controllers/{controller}/status")
    def _get_controllers_status(self, controller: str):
        ret = inspect.getfullargspec(self._get_controllers_call.function.__func__)
        self._assert_started()
        return self.sequencer._controllers[controller].get_status()


    @Post("/sequencer/controllers/{controller}/call")
    def _get_controllers_call(self, controller: str, body: FunctionCall):
        self._assert_started()
        ctrl =  self.sequencer._controllers[controller]
        ctrl : ControllerFunction
        return ctrl.call_function(body.name, body.arguments)


    @Get("/sequencer/controller/call")
    def _get_current_controller_status(self, body: FunctionCall):
        name = self.controller_name
        if name:
            return self._get_controllers_call(name, body)

    def _on_data(self, feature, data):
        with self.sequencer.data_lock:
            self.queue.put(dict(data))


    @Get("/queued_data")
    def _get_queued_data(self):
        ret = []
        while not self.queue.empty():
            ret.append(self.queue.get())
        return ret

    @Get("/sequencer/controller/status")
    def _get_current_controller_status(self):
        name = self.controller_name
        if name:
            return self._get_controllers_status(name)


    @Get("/sequencer/controller")
    def _get_current_controller(self):
        name = self.controller_name
        if name:
            return self._get_controllers_c(name)


def run(debug):
    config = SequencerConfig()
    all_features = [features.cycling, features.heart_rate]

    config.add_device(features.cycling, 'FB:6B:21:56:45:A7')
    config.add_device(features.heart_rate, 'D2:60:F3:44:A7:07')

    for x in all_features:
        config.add_ble_client(x, x, timer=1)

    for x in list_controller():
        config.add_controller(x)


    base = ControllableSequencer(config)

    if debug:
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


    all_features = [features.heart_rate, features.cycling]

    for x in all_features:
        config.add_ble_client(x, x)

    for x in list_controller():
        config.add_controller(x)

    base = ControllableSequencer(config)


    def _print(*args, self=base):
        print(f"DATA={self.data}")

    base.add_handler(_print, features.heart_rate)

    with base:
        print("Ready  1 !")

        for x in [50,100,150,200,150,220]:
            set_power(base, x, 0.5)
        base.stop()



if __name__ == '__main__':
    run(debug=True)


