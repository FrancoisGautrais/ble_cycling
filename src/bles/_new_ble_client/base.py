import json
import random
import threading
import time
from dataclasses import asdict
from abc import ABC
from pathlib import Path

from bleak import BleakClient

from bles.common.loadable import Loadable


class BaseData(ABC):
    def copy(self):
        return self.__class__(**asdict(self))


class ClientManager:
    _clients = {}

    @classmethod
    def get(cls, address):
        if address not in cls._clients:
            cls._clients[address] = BleakClient(address)

        return cls._clients[address]

class BaseDebugData:
    pass

class DebugDataList:
    @classmethod
    def from_json_file(cls, file, interval=1, loop=True, cast=None):
        return cls(json.loads(Path(file).read_text()), interval, loop, cast=cast)

    @classmethod
    def from_csv_file(cls, file, interval=1, loop=True,  cast=None, csv_sep=";"):
        data = []
        headers = None
        with open(file) as fd:
            for i, line in fd.readlines():
                if not i: headers = line.split(csv_sep)
                elif line:
                    content = line.split(csv_sep)
                    assert len(content) == len(headers)
                    data.append(dict(zip(headers, content)))

        return cls(data, interval, loop, cast)


    def __init__(self, data, interval=1, loop=True, cast=None):
        self.data = list(data)
        self.loop = loop
        self.interval = interval
        self.cast = cast

    def _cast(self, x):
        if self.cast:
            return self.cast(x)
        else:
            return x

    def __iter__(self):
        while True:
            for x in self.data:
                time.sleep(self.interval)
                yield self._cast(x)

            if not self.loop: break

class DebugDataClassList(DebugDataList):
    _data_class_ = None

    @classmethod
    def data_class(cls, classe):
        return cls.__class__(f"{classe.__name__}_DebugDataClassList", (cls,),
                             {"_data_class_": classe})

    def _cast(self, x):
        return self._data_class_(**x)






class BaseBleClient(ABC, Loadable):
    _data_class_ : type = None
    _features_ = None


    def __init__(self, address, debug=None, **params):
        self.client = ClientManager.get(address)
        self.params = params
        self._debug = self.params.get("debug")
        self._stopped = threading.Event()
        self.data :  BaseData = None
        self._handlers = []
        self._thread = None

    def set_data(self, _do_notify=True, **kwargs):
        kwargs["timestamp"] = time.time()
        if self.data is None:
            self.data = self._data_class_(**kwargs)
        else:
            self.data.__dict__.update(kwargs)

        if _do_notify:
            self._notify()
        return self.data

    def _run(self):
        if self._debug is not None:
            while not self._stopped.is_set():
                time.sleep( random.randint(990, 1010)/1000)

    def _notify(self):
        for handler in self._handlers:
            handler(self.data)

    def run_thread(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def stop(self):
        self._stopped.set()

    def add_handler(self, handler):
        self._handlers.append(handler)