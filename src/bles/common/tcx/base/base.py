from collections import OrderedDict

from bles.common.tcx.base.fields import field


class ModelBaseMeta(type):
    def __new__(cls, name, bases, attrs):
        obj = super().__new__(cls, name, bases, attrs)
        obj._init_fields()
        return obj

    def _init_fields(cls):
        if hasattr(cls, "_fields"):
            cls._fields = list(cls._fields)
            cls._fields_dict = dict(cls._fields_dict)
        else:
            cls._fields = []
            cls._fields_dict = {}

        for k, v in list(vars(cls).items()):
            if k.startswith("_") or not isinstance(v, field.Field): continue
            v.name = k
            cls._fields.append(v)
            cls._fields_dict[k] = v
            delattr(cls, k)




class ModelBase(metaclass=ModelBaseMeta):
    def __init__(self, root, data=None):
        if root is not None:
            self._affect_value(root, data)

    def _affect_value(self, root, data):
        data = data or {}
        for f in self._fields:
            if f.name in data:
                setattr(self, f.name, data[f.name])
            else:
                setattr(self, f.name, f(root))

    @classmethod
    def create(cls, **kwargs):
        for k, v in kwargs.items():
            if k not in cls._fields_dict:
                raise ValueError(f"Champ {k} indéfini pour {cls.__name__}")

        return cls(None, kwargs)





def resolve(curr, names):
    for attr in names:
        curr = getattr(curr, attr)
    return curr

class Container(list):
    _operations = {}

    @classmethod
    def register(cls, name, fct):
        cls._operations[name] = fct

    def _get_filter_function(self, **kwargs):
        functions = []
        for k, v in kwargs.items():
            names = k.split("__")
            op = None
            if len(names) == 0:
                raise Exception()
            elif len(names) == 1:
                pass
            else:
                *names, op = names
            op = self._operations[op]

            def wrapper(elem, names=names, op=op, v=v, this=self):
                curr = resolve(elem, names)
                return op(curr,  v)

            functions.append(wrapper)
        def wrap(x):
            return not functions or all(fct(x) for fct in functions)
        return wrap

    def filter(self, **kwargs):
        fct = self._get_filter_function(**kwargs)
        for x in self:
            if fct(x):
                yield x


    def group_by(self, fct, container=None):
        ret = OrderedDict()
        cls = (container or self.__class__)
        for x in self:
            label = fct(x)
            if label not in ret:
                ret[label] = cls()
            ret[label].append(x)
        return ret





def registerOp(name):
    def wrapper(fct, name=name):
        Container.register(name, fct)
        return fct
    return wrapper

@registerOp(None)
def eq(x, y):
    return x == y


@registerOp("lt")
def lt(x,y): return x < y

@registerOp("lte")
def lte(x,y): return x <= y

@registerOp("gt")
def gt(x,y): return x > y

@registerOp("gte")
def gte(x,y): return x >= y

@registerOp("ne")
def ne(x,y): return x != y

@registerOp("is")
def _is(x,y): return x is y

@registerOp("is_not")
def is_not(x,y): return x is not y

@registerOp("in")
def _in(x,y): return x is not y

@registerOp("contains")
def contains(x,y): return x is not y

