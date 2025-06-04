import copy
import threading

from bles.ble import features
from bles.ble.fitness import CyclingData
from bles.ble.heart import HRSState


class Variable:
    class Empty: pass
    _type_ = None
    _min_ = None
    _max_ = None
    _step_ = None
    _default_ = None
    _required_ = True


    def __init__(self, type=None, min=None, max=None, step=None, default=None, required=None):
        self.type = type or self._type_
        self.min = min if min is not None else self._min_
        self.max = max if max is not None else self._max_
        self.step = step if step is not None else self._step_
        self.default = default if default is not None else self._default_
        self.required = required if required is not None else self._required_

    def get_description(self):
        return {
            "type" : str(self.type),
            "min" : self.min,
            "max" : self.max,
            "step" : self.step,
            "default" : self.default,
            "required" : self.required
        }

    def resolve_values(self, parent):
        if callable(self.min):
            self.min = self.min(parent)
        if callable(self.max):
            self.max = self.max(parent)
        if callable(self.step):
            self.step = self.step(parent)
        return self

    def cast(self, v=Empty):
        if v is self.Empty:
            if self.required:
                raise ValueError()
            else:
                v = self.default
        return self.type(v) if self.type is not None else v

    def valid_value(self, v=Empty):
        if v is self.Empty:
            if self.required:
                raise ValueError()
            else:
                v = self.default

        v = self.cast(v)
        if self.min is not None and v < self.min: return self.min
        if self.max is not None and v > self.max: return self.max
        return v

    def copy(self):
        return copy.copy(self)

class TypedVariable(Variable):
    def __init__(self,  min=None, max=None, step=None, default=None, required=None):
        super().__init__(None, min, max, step, default, required)

class IntegerVar(TypedVariable):
    _type_ = int
    _step_ = 1

    def cast(self, v):
        if isinstance(v, str):
            v = v.replace(",", ".")
        return super().cast(v)

class PositiveIntegerVar(IntegerVar):
    _min_ = 0

class FloatVar(IntegerVar):
    _type_ = int
    _step_ = None

class RatioVar(FloatVar):
    _min_ = 0
    _max_ = 1
    _step_ = 0.001


class ControllerAttribute:

    def __init__(self, name, fullname=None, doc=None):
        self.name = name
        self.fullname = fullname
        self.doc = doc

    def _use(self, parent, name):
        self.parent = parent
        self.name = name
        self.fullname = self.fullname or name
        self.parent._fields[self.name] = self

    def use(self, parent, name):
        ret = copy.copy(self)
        ret._use(parent, name)
        return ret

    def get_description(self):
        return {
            "name" : self.name,
            "fullname" : self.fullname,
            "doc" : self.doc,
        }

class ControllerProperty(ControllerAttribute):

    def __init__(self, var, fullname=None, doc=None):
        super().__init__(None, fullname=fullname, doc=doc)
        self.variable = var
        self.parent :  BaseController = None

    def get_description(self):
        ret = super().get_description()
        ret.update({
            "type" : "property",
            "variable" : self.variable.get_description()
        })
        return  ret

    def set_value(self, v):
        x = self.variable.valid_value(v)
        self.parent._state[self.name] = x
        return x

    def get_value(self):
        return self.parent._state[self.name]


    def _use(self, parent, name):
        super()._use(parent, name)
        self.variable = self.variable.copy()
        self.variable.resolve_values(parent.sequencer)
        self.parent._state[name] = self.variable.default

class ControllerFunction(ControllerAttribute):

    def __init__(self, **vars):
        super().__init__(None)
        self.arguments = {}
        for k, v in vars.items():
            self.arguments[k] = v
        self.parent :  BaseController = None
        self._fct = None

    def get_description(self):
        ret = super().get_description()
        ret.update({
            "type" : "function",
            "arguments" : {k: v.get_description() for k, v in  self.arguments.items()}
        })
        return  ret

    def __call__(self, _fct=None, **kwargs):
        if self._fct is None:
            self._fct = _fct
            if self.name is None:
                self.name = _fct.__name__
            return self
        else:
            attrs = {}
            for k, v in self.arguments.items():
                attrs[k] = v.valid_value(kwargs.get(k, Variable.Empty))

            for k in kwargs:
                if k not in self.arguments:
                    raise ValueError(f"parameter {k} not available")

            return self._fct(**attrs)

    def __get__(self, instance, owner):
        ret = self.use(instance, self.name)
        ret._fct = ret._fct.__get__(instance, owner)
        return ret


    def _use(self, parent, name):
        super()._use(parent, name)
        self.arguments = {k: v.copy().resolve_values(parent.sequencer) for k, v in self.arguments.items() }




def register_controller(cls):
    assert cls._name_
    if isinstance(cls._requires_, str):
        cls._requires_ = [cls._requires_]

    BaseController._register[cls._name_] = cls
    return cls

def get_controller(name):
    return BaseController._register[name]

def list_controller():
    return list(BaseController._register)

class BaseController:
    _name_ = None
    _requires_ = None

    _register = {}


    def __init__(self, sequencer, **kwargs):
        self.kwargs = kwargs
        self.sequencer = sequencer
        self._lock = threading.Lock()
        self._connected = False
        self._pause = False
        self._fields = {}
        self._state = {}

        for k, attr in self.iter_attributes():

            attr.use(self, k)


    @classmethod
    def iter_attributes(cls, classe = None):
        classe = classe or cls
        for c in classe.__bases__:
            for k, x in cls.iter_attributes(c):
                yield k, x

        for k, v in vars(classe).items():
            if not k.startswith("_"):
                if isinstance(v, Variable):
                    v = ControllerProperty(v)
                if isinstance(v, ControllerAttribute):
                    yield k, v


    def get_status(self):
        return {
            "connected": self._connected,
            "paused" : self._pause,
            "state" : {
                k: self._state[k] for k,v in self._fields.items() if isinstance(v, ControllerProperty)
            }
        }

    @classmethod
    def get_description(cls, self = None):
        fields = dict(cls.iter_attributes())
        kwargs = {}
        if self is not None:
            kwargs["state"]={
                k: self._state[k] for k,v in self._fields.items() if isinstance(v, ControllerProperty)
            }
            kwargs["connected"] = self._connected
        return {
            "type" : cls._name_,
            "requires" : [str(x) for x in cls._requires_],
            "props" : {
                k: v.get_description() for k, v in fields.items() if isinstance(v, ControllerProperty)
            },
            "methods" : {
                k: v.get_description() for k, v in fields.items() if isinstance(v, ControllerFunction)
            },
            **kwargs
        }

    def call_function(self, name, kwargs):
        return getattr(self, name)(**kwargs)

    def get_prop(self, name):
        return self._fields[name].get_value()

    def __getitem__(self, item):
        return self._fields[item].get_value()

    def set_prop(self, name, value):
        value = self._fields[name].set_value(value)
        self._notify_change(name, value)

    def _notify_change(self, field, value):
        self._validate()

    def _connect(self):
        pass

    def _disconnect(self):
        pass

    def _on_data(self, data):
        pass

    def connect(self):
        with self._lock:
            if self._connected:
                return

        self._connect()

        with self._lock:
            self._connected = True

    def disconnect(self):
        with self._lock:
            if not self._connected:
                return

        self._disconnect()

        with self._lock:
            self._connected = False

    def send(self, data):
        with self._lock:
            paused = self._pause

        if not paused:
            self._on_data(data)

    def pause(self):
        with self._lock:
            self._pause = True

    def resume(self):
        with self._lock:
            self._pause = False


    @ControllerFunction()
    def validate(self):
        self._validate()

    def _validate(self):
        pass


@register_controller
class PowerController(BaseController):
    _name_ = "power"
    _requires_ = {features.cycling}

    power = IntegerVar(lambda x: x.get_client(features.cycling).power_range[0],
                            lambda x: x.get_client(features.cycling).power_range[1],
                            step=10, default=100)

    def _on_data(self, data):
        if isinstance(data, CyclingData):
            pass
        else:
            raise TypeError(f"{data.__class__} not handled")

    def _validate(self):
        client = self.sequencer.get_client(features.cycling)
        client.set_power(self["power"])

    @ControllerFunction(power=power)
    def set_power(self, power):
        self.set_prop("power", power)
        self.validate()

@register_controller
class ResistanceController(BaseController):
    _name_ = "resistance"
    _requires_ = {features.cycling}

    resistance = IntegerVar(lambda x: x.get_client(features.cycling).resistance_range[0],
                            lambda x: x.get_client(features.cycling).resistance_range[1],
                            step=10, default=0)

    def _on_data(self, data):
        if isinstance(data, CyclingData):
            pass
        else:
            raise TypeError(f"{data.__class__} not handled")

    @ControllerFunction()
    def set_resistance(self, resistance):
        self.set_prop("resistance", resistance)
        self.validate()

@register_controller
class SimulationController(BaseController):
    _name_ = "simulation"
    _requires_ = {features.cycling}

    wind = FloatVar(default=0)
    grade = FloatVar(default=0)
    cr = FloatVar(default=0)
    cw = FloatVar(default=0)

    @ControllerFunction(wind=wind, grade=grade, cr=cr, cw=cw)
    def set_simulation_params(self, **kwargs):
        for k, v in kwargs.items():
            self._fields[k].set_value(v)

        self.validate()

    def _on_data(self, data):
        if isinstance(data, CyclingData):
            pass
        else:
            raise TypeError(f"{data.__class__} not handled")


@register_controller
class HeartRateController(BaseController):
    _name_ = "heart_rate"
    _requires_ = {features.cycling, features.heart_rate}

    bpm = IntegerVar()

    def __init__(self, sequencer, **kwargs):
        super().__init__(sequencer, **kwargs)
        self.power_min = sequencer.get_client(features.cycling).power_range[0]
        self.power_max = sequencer.get_client(features.cycling).power_range[1]

    def _on_data(self, data):
        if isinstance(data, CyclingData):
            pass
        elif isinstance(data, HRSState):
            pass
        else:
            raise TypeError(f"{data.__class__} not handled")


    @ControllerFunction()
    def set_bpm(self, bpm):
        self.set_prop("bpm", bpm)
        self.validate()




