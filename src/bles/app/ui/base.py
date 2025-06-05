import contextlib
import math
from collections import defaultdict

import dearpygui.dearpygui as dpg

from bles.common.tcx.model import TCX


def _log(sender, app_data):
    print(sender, app_data)
    print(dpg.last_item())

def get_data(keys="speed_kmh"):
    #data = TCX.from_file("/home/fanch/Programmation/python/home_trainer/data/Zepp20250307080754.tcx")
    #data = TCX.from_file("/home/fanch/Programmation/python/home_trainer/data/Zepp20250317155149.tcx")
    data = TCX.from_file("/home/fanch/Programmation/python/home_trainer/data/Zepp20250320181302.tcx")
    points = data.activities[0].laps[0].points
    ret = points.group_by(lambda x: (x.distance // 100)*10)
    #d = ZippedData(ret, key_y="speed_kmh",  name="test")

    if isinstance(keys, str):
        keys = [keys]

    return [ ObjectListData(points, key_y=k,  name=k) for k in keys]


class EventManager:
    DOUBLE_CLICK= "doubleclick"
    def __init__(self):
        self._regiseterd = defaultdict(dict)


    def _call(self, sender, app_data, user_data):
        ret = self._regiseterd[user_data]
        print("dsdfsdf",sender,  ret, self._regiseterd)
        if sender in ret:
            ret[sender]()

    def init(self):

        with dpg.handler_registry():
            dpg.add_mouse_double_click_handler(callback=self._call, user_data=self.DOUBLE_CLICK)

    def register(self, sender, event, fct):
        self._regiseterd[event][sender] = fct


event_manager = EventManager()

register_event = event_manager.register
class App:
    SIZE=(1600,800)

    def __init__(self):
        dpg.create_context()
        dpg.create_viewport(title='Custom Title', width=self.SIZE[0], height=self.SIZE[1])
        event_manager.init()

        with Window(label="Dear PyGui Demo", width=self.SIZE[0], height=self.SIZE[1], on_close=self.on_close, pos=(100, 100),
                        tag="__demo_id"):
            with dpg.group(horizontal=False) as item:
                Stats(get_data("speed_kmh" ))
                Stats(get_data("bpm" ))





    def on_close(self):
        pass

    def show(self):
        dpg.set_primary_window("__demo_id", True)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()


class BaseWidget:
    _main_function_ = None
    _default_params_ = {

    }

    def __init__(self, *args, **kwargs):
        data = dict(self._default_params_ or {})
        data.update(kwargs)
        if self._main_function_:
            with self._main_function_.__func__(*args, **data) as item:
                self.id = item
                self.init()
        else:
            self.init()

    def register_event(self, signal, fct):
        if isinstance(signal, str):
            signal = [signal]

        for sig in signal:
            event_manager.register(self.id, sig, fct)

    def init(self):
        pass

    def __enter__(self):
        dpg.push_container_stack(self.id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        dpg.pop_container_stack()

class Window(BaseWidget):
    _main_function_ = dpg.window

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

@contextlib.contextmanager
def Item(x):
    dpg.push_container_stack(x)
    yield
    dpg.pop_container_stack()

class StatData:
    def __init__(self, name=None, x=None, y=None ):
        self._X = x
        self._Y = y
        self.name = name

    def get_data(self):
        return self.X, self.Y

    def filter(self, fct):
        X, Y = [], []
        for x,y in zip(self.get_data()):
            if fct(x,y):
                X.append(x)
                Y.append(y)
        return StatData(self.name, X, Y)

    @property
    def X(self):
        return self._X

    @property
    def Y(self):
        return self._Y

def get_attr_fct(v, ):
    if callable(v):
        return v
    if isinstance(v, str):
        return lambda x, n=v: getattr(x, n)
    return lambda x: x

class ListData(StatData):
    def __init__(self, Y, X=None, name=None):
        super().__init__(name)
        self._Y = Y
        self._X = X if X is not None else list(range(len(self._Y)))

class FunctionData(ListData):
    def __init__(self, fct, X, name=None):
        self.fct = fct
        super().__init__([fct(x) for x in X], X, name=name)

    def update(self, X):
        self._X = X
        self._Y = [self.fct(x) for x in self._X]


class ZippedData(ListData):
    def __init__(self, data, name=None, key_x=None, key_y=None):
        get_x = get_attr_fct(key_x)
        get_y = get_attr_fct(key_y)
        if isinstance(data, dict): data = list(data.items())
        X, Y = [], []
        for x, y in data:
            X.append(get_x(x))
            Y.append(get_y(y))
        super().__init__(Y, X, name=name)


class ObjectListData(ListData):
    def __init__(self, data, key_y, key_x=None, name=None):
        get_y = None
        get_x = None
        if isinstance(key_y, str):
            get_y = lambda x, n=key_y: getattr(x, n)
        elif callable(key_y):
            get_y =key_y
        else:
            raise ValueError()

        if isinstance(key_x, str):
            get_x = lambda x, n=key_x: getattr(x, n)
        elif callable(key_x):
            get_x = key_x

        X, Y = [], []
        for i, obj in enumerate(data):
            Y.append(get_y(obj))
            if get_x is None:
                X.append(i)
            else:
                X.append(get_x(obj))

        super().__init__(Y, X, name=name)


class SelectionRange(BaseWidget):


    def __init__(self, parent, color=(255,0,0), on_chnage=None, **kwargs):
        self.parent = parent
        self.x_axis = parent.x_axis
        self.y_axis = parent.y_axis
        self.color = color
        self._on_change_fct = on_chnage
        self.fill_color = list(color) + [80]
        super().__init__( **kwargs)

        self.start_bar = dpg.add_drag_line(default_value=100, vertical=True,
                               callback=self._on_change, color=self.color,
                                show=False)
        self.end_bar = dpg.add_drag_line(default_value=600, vertical=True,
                               callback=self._on_change, color=self.color,
                                show=False)

        self.circle = dpg.add_drag_point(
            default_value=(600,300),
            color=self.color,
            callback=self._on_change,
            thickness=1,
            show=False
        )



        self.rect = dpg.draw_rectangle(
                    pmin=[2, -1.5],
                    pmax=[6, 1.5],
                    color=self.color,
                    fill=self.fill_color,
                    thickness=0,
            show=False
                )


        self._to_show =  (self.rect, self.start_bar, self.end_bar, self.circle)

    def show(self):

        print("show !")
        for item in self._to_show:
            dpg.configure_item(item, show=True)

        a, b = dpg.get_axis_limits(self.x_axis)
        r = (b-a) / 2
        self.update((a + r/3, a + 2*r/3))
    def hide(self):

        print("hide !")
        for item in self._to_show:
            dpg.configure_item(item, show=False)

    def get_value(self):
        a, b = dpg.get_value(self.start_bar), dpg.get_value(self.end_bar)
        if a>b: a,b = b,a
        return (a, b)

    def update(self, range=None):
        if range:
            a, b = range
        else:
            a, b = self.get_value()
        x_mid = a + (b-a)/2
        center =  (x_mid, self.parent.get_center()[1])
        dpg.set_value(self.circle,center)
        dpg.set_value(self.start_bar, a)
        dpg.set_value(self.end_bar, b)
        dpg.configure_item(self.rect,
                           pmin=[a, -1e5], pmax=[b, 1e5])

        if self._on_change_fct:
            self._on_change_fct((a,b))

    def _on_change(self, sender, app_data, user_data):
        self.update()

class Stats(BaseWidget):
    _main_function_ = dpg.plot
    _default_params_ = {
        "width" : -1,
        "height" : 300
    }
    def __init__(self, data, label_x="x", label_y="y", **kwargs):
        self.label_x=label_x
        self.label_y=label_y
        self.data = [data] if not isinstance(data, (list, tuple)) else data
        self._range_visible = False


        for x in self.data:
            assert isinstance(x, StatData)
        super().__init__(**kwargs, callback=self._callback)


    def _callback(self, *args):
        pass

    def toggle_range(self):
        print(f"toggle_range")
        if self._range_visible:
            self.range.hide()
        else:
            self.range.show()
        self._range_visible = not self._range_visible


    def on_range_change(self, range):
        x1, x2 = range
        x1 = int(x1)
        x2 = int(x2)
        print(x1 , x2)


    def init(self):
        self.legend = self.plot_legend()
        self.x_axis = self.plot_x()
        self.y_axis = self.plot_y()
        with Item(self.y_axis):
            self.draw()
            self.btn = dpg.add_button(label="Afficher", callback=self.toggle_range)


        self.range = SelectionRange(self, on_chnage=self.on_range_change)


    def get_center(self):
        x1, x2 = dpg.get_axis_limits(self.x_axis)
        y1, y2 = dpg.get_axis_limits(self.y_axis)
        return (x1 + (x2-x1)/2),( y1 + (y2-y1)/2)

    def plot_legend(self):
        return dpg.add_plot_legend()

    def plot_x(self):
        return dpg.add_plot_axis(dpg.mvXAxis, label=self.label_x)

    def plot_y(self):
        return dpg.add_plot_axis(dpg.mvYAxis, label=self.label_y)

    def draw(self):
        min_x = []
        max_x = []
        min_y = []
        max_y = []
        for x in self.data:
            X, Y = x.get_data()
            min_x.append(min(X))
            min_y.append(min(Y))
            max_x.append(max(X))
            max_y.append(max(Y))

            dpg.add_line_series(X, Y, label=x.name)

        dpg.set_axis_zoom_constraints(self.x_axis, min(min_x), max(max_x))
        dpg.set_axis_limits_constraints(self.x_axis, min(min_x), max(max_x))
        dpg.set_axis_zoom_constraints(self.y_axis, min(min_y), max(max_y))
        dpg.set_axis_limits_constraints(self.y_axis, min(min_y), max(max_y))
        dpg.show_style_editor()





App().show()
