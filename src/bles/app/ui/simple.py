import signal
import threading
import time
import tkinter as tk
from tkinter  import *

import requests

from bles.api import ServerInterface
from bles.common.config import config
from bles.common.timer import Timer
from bles.core.driver.base import BaseDriver
from bles.core.sequencer.base import ControllableSequencer
from bles.core.simulator.base_simulator import PowerSimulator
from tkinter import messagebox, ttk

from bles.app.stats.base import Stat, Point


class ApiException(Exception):
    pass

class ApiDriver(BaseDriver):

    def __init__(self, host, port, timer_period=None, on_data=None, debug=True):
        self.host = host
        self.port = port
        self._started = False
        self._paused = False
        self._debug = debug
        self._timer = None
        self._on_data_handler = on_data
        self._status = None
        self._current_controller = None
        self.timer_period = timer_period

    def init(self):
        while True:
            try:
                self.get_status()
            except:
                time.sleep(0.3)
                continue
            break

        if self.timer_period:
            self._timer = Timer(self._on_timer, self.timer_period)
            self._timer.start()
        self.start_timer()

    def start_timer(self):
        if self.timer_period and not self._timer:
            self._timer = Timer(self._on_timer, self.timer_period)
            self._timer.start()

    def _on_timer(self):
        if self._started and not self._paused:
            data = self._get_queued_data()
            if self._on_data_handler is None: return
            for d in data:
                self._on_data_handler("", d)


    def stop_timer(self):
        if self._timer: self._timer.stop()

    def _get(self, url, **kwargs):
        return requests.get(f"http://{self.host}:{self.port}{url}", **kwargs)


    def _post(self, url, **kwargs):
        return requests.post(f"http://{self.host}:{self.port}{url}", **kwargs)


    def _assert_app_running(self):
        if self._status is None or self._status["status"] != "RUNNING":
            raise ApiException(f"L'application n'est pas en cours")


    def _assert_app_started(self):
        if self._status is None or self._status["status"] not in ("RUNNING", "PAUSED"):
            raise ApiException(f"L'application n'est pas en cours")

    def get_controller_name(self):
        return self._current_controller

    def use_controller(self, name):
        self._current_controller = name
        self._get(f"/sequencer/controllers/{name}/use")

    def on_data(self, feature, data):
        pass

    def pause(self):
        if self._started:
            self._get("/sequencer/pause")
            self._paused = True
        else:
            raise ApiException(f"L'application n'est pas lancé")

    def resume(self):
        if not self._started:
            self._get("/sequencer/resume")
            self._paused = False
        else:
            raise ApiException(f"L'application n'est pas lancé")

    def start(self):
        self._get("/sequencer/start")
        self._started = True
        self._paused = False

    def stop(self):
        self._get("/sequencer/stop")
        self._started = False
        self._paused = False

    def get_status(self):
        ret = self._get("/sequencer/status")
        self._status =  ret.json()
        return self._status


    def _get_queued_data(self):
        ret = self._get("/queued_data")
        return ret.json()


    def ctrl_set_prop(self, name, value):
        ret = self._get(f"/sequencer/controller/prop/{name}/{value}")
        return ret.json()

    def ctrl_get_prop(self, name, value):
        ret = self._get(f"/sequencer/controller/prop/{name}/{value}")
        return ret.json()

    def ctrl_call_function(self, name, data):
        payload = {
            "name" : name,
            "arguments" : {"power" : data}
        }
        ret =  self._post(f"/sequencer/controller/call", json=payload)
        print("heere", payload, ret.json())
        return ret.json()

class LocalApiDriver:
    def __init__(self, on_data, debug=False):
        self._sequencer = None
        self._server = None
        self.driver = None
        self._on_data_handler = on_data
        self._debug = debug

    def server_start(self):
        self._sequencer = ControllableSequencer(config.sequencer)
        self._server = ServerInterface(
            host=config.app_host,
            port=config.app_port,
            sequencer=self._sequencer)
        self._server.run_server(True)
        self.driver = ApiDriver(config.app_host, config.app_port, 1, on_data=self._on_data_handler)
        if self._debug:
            self._sequencer.use_simulator(PowerSimulator(init_freq=80))

        self.driver.init()


    def server_stop(self):
        if self._server:
            self._server.stop()
            self._server.join()
            self._server = None
        self.driver.stop_timer()



class Api:

    def __init__(self, debug=True):
        self._started = False
        self._paused = False
        self._debug = debug
        self._server = None
        self._sequencer = None
        self._timer = None
        self._status = None


    def _get(self, url, **kwargs):
        host = config.app_host
        port = config.app_port
        return requests.get(f"http://{host}:{port}{url}", **kwargs)

    def _post(self, url, **kwargs):
        host = config.app_host
        port = config.app_port
        return requests.post(f"http://{host}:{port}{url}", **kwargs)


    def _assert_app_running(self):
        if self._status is None or self._status["status"] != "RUNNING":
            raise ApiException(f"L'application n'est pas en cours")


    def _assert_app_started(self):
        if self._status is None or self._status["status"] not in ("RUNNING", "PAUSED"):
            raise ApiException(f"L'application n'est pas en cours")

    def app_status(self):
        ret = self._get("/sequencer/status")
        self._status =  ret.json()
        return self._status


    def app_queued_data(self):
        ret = self._get("/queued_data")
        return ret.json()


    def app_start(self):
        self._get("/sequencer/start")
        self._started = True
        self._paused = False

    def app_stop(self):
        self._get("/sequencer/stop")
        self._started = False
        self._paused = False

    def app_pause(self):
        if self._started:
            if self._paused:
                self._get("/sequencer/resume")
                self._paused = False
            else:
                self._get("/sequencer/pause")
                self._paused = True
        else:
            raise ApiException(f"L'application n'est pas lancé")

    def app_use(self, name):
        self._assert_app_started()
        self._get(f"/sequencer/controllers/{name}/use")

    def app_set_power(self, power):
        self._assert_app_running()
        return self.app_call_controller("set_power", {"power": power}, controller="home_trainer")

    def app_get_controller_status(self, controller=None):
        self._assert_app_started()
        if controller:
            return self._get(f"/sequencer/controllers/{controller}/status")
        else:
            return self._get(f"/sequencer/controller/status")

    def app_call_controller(self, name, data, controller=None):
        self._assert_app_started()
        payload = {
            "name" : name,
            "arguments" : data
        }

        if controller:
            name = self._status and self._status["current_controller"]
            if name != controller:
                self.app_use(controller)
            return self._post(f"/sequencer/controllers/{controller}/call", json=payload, headers={"Content-Type": "application/json"})
        else:
            return self._post(f"/sequencer/controller/call", json=payload)



    def server_start(self):

        self._timer = Timer(self._on_timer)
        self._timer.start()
        self._sequencer = ControllableSequencer(config.sequencer)
        self._server = ServerInterface(
            host=config.app_host,
            port=config.app_port,
            sequencer=self._sequencer)
        self._server.run_server(True)
        if self._debug:
            self._sequencer.use_simulator(PowerSimulator(init_freq=80))

    def _on_timer(self):
        raise NotImplementedError()

    def server_stop(self):
        if self._server:
            self._server.stop()
            self._server.join()
            self._server = None
        if self._timer:
            self._timer.stop()


def wrap_api_error(fct):
    def wrapper(*args, **kwargs):
        try:
            return fct(*args, **kwargs)
        except ApiException as err:
            messagebox.showerror("Erreur", str(err))
    return wrapper





class TkApp(tk.Tk):

    def __init__(self, auto_start=True):
        tk.Tk.__init__(self)
        self.api = LocalApiDriver(self._on_data, True)
        signal.signal(signal.SIGINT, self.handler)
        self.auto_start = auto_start
        self.geometry("600x400")
        self.stats = None
        self.peak = Point()
        self.started = False
        self.paused = False
        self.power_value = IntVar(self, value=100)
        self.power_text = StringVar(self)
        self.stat_lock = threading.Lock()

        self.title("Application")




        frame = tk.Frame(self)
        frame.pack(side=TOP,expand=False, fill=X)

        self._btn_pause = tk.Button(frame, text="Pause / Resume", command=self._toggle_pause)
        self._btn_pause.pack(side=RIGHT, expand=True, fill=X)

        self._btn_start = tk.Button(frame, text="Ecouter", command=self._toggle_start)
        self._btn_start.pack(side=RIGHT, expand=True, fill=X)




        self.frame_info = self._frame_info()



        self.status_label = tk.Label(self, text="")
        self.status_label.pack(side=BOTTOM, expand=True, fill=X)
        self.status_label["text"] = "L'application n'écoute pas"
        frame_power = self._frame_power()
        frame_power.pack(side=BOTTOM, expand=True, fill=X)


        self.api.server_start()

    def show_infos(self):
        self.frame_info.pack(side=TOP, expand=True, fill=X)

    def hide_info(self):
        self.frame_info.pack_forget()

    def _change_power_value(self, x):
        x = int(int(x) / 10) * 10
        self.power_text.set(f"{x} W")

    @wrap_api_error
    def _set_power(self):

        self.api.driver.use_controller("home_trainer")
        self.api.driver.ctrl_call_function("set_power", self.power_value.get())

    def _frame_power(self):
        f = tk.Frame(self)
        scale = Scale(f, from_=0, to=2000,
                      orient=HORIZONTAL,
                      variable=self.power_value,
                      showvalue=True,
                      command=self._change_power_value)

        scale.pack(side=LEFT, expand=True, fill=X)
        label = Label(f, textvariable=self.power_text)
        label.pack(side=LEFT, expand=True, fill=X)
        envoyer = Button(f, text="Envoyer", command=self._set_power)
        envoyer.pack(side=LEFT, expand=True, fill=X)

        self._change_power_value(100)
        return f

    def _frame_info(self):
        f = ttk.Frame(self, padding=(10,10,10,10))


        kwargs = {
            "font" : ('utopia', 20)
        }
        frame = tk.Frame(f)
        frame.pack(side=TOP, expand=True, fill=X)

        tk.Label(frame, text="Speed", **kwargs).pack(side=LEFT, expand=True, fill=X)
        self._speed = tk.Label(frame, text="0", **kwargs)
        self._speed.pack(side=LEFT, expand=True, fill=X)
        self._speed_avg = tk.Label(frame, text="0", **kwargs)
        self._speed_avg.pack(side=LEFT, expand=True, fill=X)
        self._speed_max = tk.Label(frame, text="0", **kwargs)
        self._speed_max.pack(side=LEFT, expand=True, fill=X)

        frame = tk.Frame(f)
        frame.pack(side=TOP, expand=True, fill=X)

        tk.Label(frame, text="Power", **kwargs).pack(side=LEFT, expand=True, fill=X)
        self._power = tk.Label(frame, text="0", **kwargs)
        self._power.pack(side=LEFT, expand=True, fill=X)
        self._power_avg = tk.Label(frame, text="0", **kwargs)
        self._power_avg.pack(side=LEFT, expand=True, fill=X)
        self._power_max = tk.Label(frame, text="0", **kwargs)
        self._power_max.pack(side=LEFT, expand=True, fill=X)


        frame = tk.Frame(f)
        frame.pack(side=TOP, expand=True, fill=X)

        tk.Label(frame, text="Bpm", **kwargs).pack(side=LEFT, expand=True, fill=X)
        self._bpm = tk.Label(frame, text="0", **kwargs)
        self._bpm.pack(side=LEFT, expand=True, fill=X)
        self._bpm_avg = tk.Label(frame, text="0", **kwargs)
        self._bpm_avg.pack(side=LEFT, expand=True, fill=X)
        self._bpm_max = tk.Label(frame, text="0", **kwargs)
        self._bpm_max.pack(side=LEFT, expand=True, fill=X)

        return f

    @wrap_api_error
    def _toggle_start(self):
        if not self.api._server:
            raise ApiException(f"Le serveur n'est pas lancé")
        if self.api.driver._started:
            self.api.driver.stop()
            self._btn_start["text"] = "Ecouter"
            with self.stat_lock:
                self.stats = None
            self.status_label["text"] = "L'application n'écoute pas"
            self.hide_info()
        else:
            with self.stat_lock:
                self.stats = Stat()

            for i in range(100):
                try:
                    self.api.driver.start()
                    break
                except requests.exceptions.ConnectionError as err:
                    time.sleep(0.1)

            self._btn_start["text"] = "Arreter"
            self.status_label["text"] = "Connection...."
            self._poll_status()
    
    @wrap_api_error
    def _toggle_pause(self):
        if not self.api._server:
            raise ApiException(f"Le serveur n'est pas lancé")
        if not self.api.driver._started:
            raise ApiException(f"L'application n'est pas lancé")
        self.api.driver.pause()


    def _on_timer(self):
        if self._started and not self._paused:
            data = self.app_queued_data()
            with self.stat_lock:

                if not self.stats: return
                for d in data:
                    self.stats.append(d)

                if not self.stats.last: return
                self._power["text"] = f"{int(self.stats.last.power)}"
                self._power_avg["text"] = f"{int(self.stats.avg.power)}"
                self._power_max["text"] = f"{int(self.stats.max.power)}"

                self._speed["text"] = f"{int(self.stats.last.speed)}"
                self._speed_avg["text"] = f"{int(self.stats.avg.speed)}"
                self._speed_max["text"] = f"{int(self.stats.max.speed)}"

                self._bpm["text"] = f"{int(self.stats.last.bpm)}"
                self._bpm_avg["text"] = f"{int(self.stats.avg.bpm)}"
                self._bpm_max["text"] = f"{int(self.stats.max.bpm)}"


    def _on_data(self, feature, d):
        print("data recieved !!!")
        with self.stat_lock:

            if not self.stats: return
            self.stats.append(d)

            if not self.stats.last: return
            self._power["text"] = f"{int(self.stats.last.power)}"
            self._power_avg["text"] = f"{int(self.stats.avg.power)}"
            self._power_max["text"] = f"{int(self.stats.max.power)}"

            self._speed["text"] = f"{int(self.stats.last.speed)}"
            self._speed_avg["text"] = f"{int(self.stats.avg.speed)}"
            self._speed_max["text"] = f"{int(self.stats.max.speed)}"

            self._bpm["text"] = f"{int(self.stats.last.bpm)}"
            self._bpm_avg["text"] = f"{int(self.stats.avg.bpm)}"
            self._bpm_max["text"] = f"{int(self.stats.max.bpm)}"



    def handler(self, signal_received, frame):
        # Handle any cleanup here
        print('SIGINT or CTRL-C detected. Exiting gracefully')
        self.api.driver.stop()
        exit(0)

    def show(self):
        if self.auto_start:
            self.after(100, self._toggle_start)
        self.mainloop()

    def _poll_status(self):
        try:
            self.api.driver.get_status()
            if self.api.driver._status["status"] == "CONNECTING":
                raise Exception()

            self.status_label["text"] = "Connecté !"
            self.show_infos()
        except Exception as err:
            self.after(500, self._poll_status)



    def destroy(self):
        if self.stats:
            self.stats.close()
        self.api.driver.stop()
        super().destroy()


class Window(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.bind("<Escape>", self.destroy())


if __name__ == '__main__':
    TkApp().show()
