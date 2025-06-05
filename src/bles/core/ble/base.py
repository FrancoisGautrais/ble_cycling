import asyncio
import os
import threading
import time
from abc import ABC, abstractmethod
from queue import Queue

from bleak import BleakClient


class FeatureNotAvailable(Exception): pass


class Message:
    _name_ = None
    def __init__(self, name=None, **kwargs):
        self.name = name if name is not None else self._name_
        self.kwargs = kwargs

    def __repr__(self):
        return f"<Message {self.name} {self.kwargs}>"


class Exit(Message):
    _name_ = "exit"


class SetValue(Message):
    _name_ = "set_value"
    _field_ = None
    def __init__(self, value, **kwargs):
        self.field = self._field_
        self._value = value
        super().__init__(**kwargs)

    @property
    def value(self):
        return self._value

def register_ble_client(cls):
    if cls._feature_ not in BaseBleClient._registered:
        BaseBleClient._registered[cls._feature_] = {False: None, True: None}
    BaseBleClient._registered[cls._feature_][cls._debug_] = cls

    return cls


def get_ble_client(feature, debug):
    return BaseBleClient._registered[feature][debug]



class BaseBleClient(ABC):

    _data_class_ : type = None
    _feature_ = None
    _debug_ = False

    _registered = {}

    def __init__(self):
        self.start_time = time.time()
        self.data = None
        self._connection_event = threading.Event()
        self._thread = None
        self._on_disconnect = None
        self._on_connect = None
        self._handlers = []

    def get_status(self):
        return {
            "connected" : self.is_connected,
        }

    def _thread_main(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def _notify(self):
        for handler in self._handlers:
            handler(self._feature_, self.data)

    def _get_time(self):
        return time.time() - self.start_time

    def _set_data(self, **kwargs):
        kwargs["timestamp"] = self._get_time()
        if self.data is not None:
            self.data.__dict__.update(kwargs)
        else:
            self.data = self._data_class_(**kwargs)

        self._notify()


    def run_thread(self):
        self._thread = threading.Thread(target=self._thread_main)
        self._thread.start()


    def join(self):
        if self._thread:
            self._thread.join()
            self._thread = None

    def add_handler(self, handler):
        self._handlers.append(handler)

    def remove_handler(self, handler):
        self._handlers.remove(handler)


    @property
    def is_connected(self):
        raise NotImplementedError()

    def _on_disconnect_wrapper(self, client):
        self._connection_event.set()
        if self._on_disconnect:
            self._on_disconnect(self)

    def on_disconnect(self, fct):
        self._on_disconnect = fct

    def on_connect(self, fct):
        self._on_connect = fct

    def wait_for_connection(self, timeout):
        if self.is_connected: return True
        self._connection_event.clear()
        return self._connection_event.wait(timeout)

class EventMixin:

    def __init__(self):
        self._changed = threading.Event()
        self.queue = Queue()
        self.do_continue = True


    def _add_event(self, event):

        if isinstance(event, type) and issubclass(event, Message):
            event = event()
        self.queue.put(event)
        self._changed.set()

    def stop(self):
        self._add_event(Exit())


class BleClient(EventMixin, BaseBleClient):

    def __init__(self, addresse):
        BaseBleClient.__init__(self)
        EventMixin.__init__(self)
        self._driver = addresse
        if isinstance(self._driver, str):
            self._driver = BleakClient(addresse)
        self._driver.set_disconnected_callback(self._on_disconnect_wrapper)

    @property
    def is_connected(self):
        return self._driver.is_connected

    def get_status(self):
        data = super().get_status()
        data.update({
            "address" : self.addresse
        })
        return data


    async def __aenter__(self):
        print(f"Connecting to {self}")
        ret = await self._driver.__aenter__()
        print(f"Driver loaded for {self}")
        await self._start_service()
        self._connection_event.set()
        print(f"Connected to {self}")
        if self._on_connect:
            self._on_connect(self)

        return ret


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._stop_services()
        return await self._driver.__aexit__(exc_type, exc_val, exc_tb)


    async def bt_task(self):
        async with self:
            while self.do_continue:
                await asyncio.sleep(1)

    async def cmd_task(self):
        timer = 1
        while self.do_continue:
            last_timer = time.time()
            while self.do_continue:
                while not self.queue.empty():
                    next = self.queue.get()
                    assert isinstance(next, Message)
                    if isinstance(next, Exit):
                        self.do_continue = False
                        return
                    else:
                        await self._on_message(next)

                sleep_time = None
                do_wait = True
                if timer is not None:
                    next = timer + last_timer
                    sleep_time = next - time.time()
                    if sleep_time<=0: do_wait=False

                if self.do_continue:
                    self._changed.clear()
                    if sleep_time and sleep_time>0:
                        await asyncio.sleep(sleep_time)

                last_timer = time.time()


    async def _athread_main(self):
        self.do_continue = True
        loop = asyncio.get_running_loop()
        bt_task = asyncio.create_task(self.bt_task() )
        cmd_task = asyncio.create_task(self.cmd_task() )
        await asyncio.wait([bt_task, cmd_task], return_when=asyncio.FIRST_COMPLETED)
        bt_task.cancel()

    def _thread_main(self):
        asyncio.run(self._athread_main())



    @abstractmethod
    async def _start_service(self):
        pass

    @abstractmethod
    async def _stop_services(self):
        pass

    @abstractmethod
    async def _on_message(self, message):
        pass


