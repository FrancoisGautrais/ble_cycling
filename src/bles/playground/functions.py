import math
from functools import partial

import numpy as np
from matplotlib import pyplot as plt

class Line(list):
    def __init__(self, Y, label=None):
        super().__init__(Y)
        self.label = label

class Function:
    def __init__(self, fct, pre=None, label=None, **kwargs):
        self.kwargs = kwargs
        self.pre = pre
        self.fct = fct
        self.label = label
        self._line_kwargs = {
            "label" : label
        }

    def __call__(self, *xs, **kwargs):
        return self.fct(*xs, **kwargs, **self.kwargs)

    def vector(self, *args, **kwargs):
        headers = list(kwargs)
        if not kwargs and args:
            x = {}
            _kwargs = [x for _ in range(len(args[0]))]
        else:
            _kwargs = [{k: v[i] for i, k in enumerate(headers) } for  v in zip(*kwargs.values())]
        return Line([self.fct(*x, **kw, **self.kwargs) for *x, kw in zip(*args, _kwargs)], **self._line_kwargs)

    def __add__(self, other):
        return AddFunc(self, other)

    def __truediv__(self, other):
        return DivFunc(self, other)

    def __mul__(self, other):
        return MultFunc(self, other)

    def __sub__(self, other):
        return SubFunc(self, other)

F = Function

class VectorFunc(Function):

    def __call__(self, *xs, **kwargs):
        return self.vector(*xs, **kwargs)

V = VectorFunc


X1 = [0,1,2,3,4]
X2 = [4,5,6,7,8]
data = {
    "a1" : [10,11,12,13,14],
    "b1" : [20,21,22,23,24],
    "c1" : [30,31,32,33,34],
}

def _test(*args, **kwargs):
    print(args, kwargs)

def fun(*args, **kwargs):
    headers = list(kwargs)
    if not kwargs and args:
        x = {}
        _kwargs = [x for _ in range(len(args[0]))]
    else:
        _kwargs = [{k: v[i] for i, k in enumerate(headers) } for  v in zip(*kwargs.values())]
    return [_test(*x, **kw) for *x, kw in zip(*args, _kwargs)]




def show(X, *Yn):
    fig, ax = plt.subplots()  # Create a figure containing a single Axes.
    for i, Y in enumerate(Yn):
        label = f"Fct {i + 1}"
        if isinstance(Y, Line):
            label = Y.label
        ax.plot(X, Y, label=label)  # Plot some data on the Axes.
    plt.legend()
    plt.show()


def exp(ratio, steepness=10, midpoint=0.75):
    maxi = (1 + math.exp(-steepness * (-midpoint)))
    mini = (1 + math.exp(-steepness * (1-midpoint)))
    if mini > maxi:
        mini, maxi = maxi, mini
    return ((1 + math.exp(-steepness * (ratio - midpoint)))-mini) / (maxi - mini)

def exp_inv(ratio, steepness=10, midpoint=0.75):
    return exp(1 - ratio, steepness=steepness, midpoint=midpoint)

def exp_opp(ratio, steepness=10, midpoint=0.75):
    return 1-exp(ratio, steepness=steepness, midpoint=midpoint)

def exp_opp_inv(ratio, steepness=10, midpoint=0.75):
    return 1-exp(1 - ratio, steepness=steepness, midpoint=midpoint)

def exp_cb( steepness=10, midpoint=0.75, inv=False, opp=False,  label=None):
    if not inv and not opp:
        cb = exp
    elif not inv and opp:
        cb = exp_opp
    elif inv and not opp:
        cb = exp_inv
    else:
        cb = exp_opp_inv
    return F(cb, steepness=steepness, midpoint=midpoint, label=label)


def draw_function(X, *fcts, _Xaxis=None):
    X = list(X)
    if _Xaxis is None:
        _Xaxis = X
    Ys = []
    for f in fcts:
        if isinstance(f, Function):
            Ys.append(f.vector(X))
        else:
            Ys.append([f(x) for x in X])
    show(_Xaxis, *Ys)



def ratio_serie(count=100):
    return [x/count for x in range(count+1)]


def power_serie():
    return list(range(80,300))

def bpm_series(start, end):
    ret = []
    while start<=end:
        ret.append(start)
        start+=1
    return ret

def draw_ratio_function(*fcts, _Xaxis=None):
    return draw_function(ratio_serie(), *fcts)


class FunctionOperation(Function):

    def __init__(self,  *functions, merge_fun=None,  **kwargs):
        super().__init__(self._wrapper,  **kwargs)
        self._functions = list(functions)
        self.merge_fun = merge_fun

    def _wrapper(self, *args):
        vec = [fct(*args) for fct in self._functions]
        return self.merge(vec)


    def merge(self, values):
        if self.merge_fun:
            return self.merge_fun(*values)
        raise NotImplementedError()



class AddFunc(FunctionOperation):
    def merge(self, values):
        return sum(values)


class SubFunc(FunctionOperation):
    def merge(self, values):
        a, b = values
        return a-b

class MultFunc(FunctionOperation):
    def merge(self, values):
        ret = 1
        for x in values: ret*=x
        return x

class DivFunc(FunctionOperation):
    def merge(self, values):
        a, b = values
        return a/b


def dec(x, point=0.5, alpha=-0.2):
    if x<point: return 0
    if point:
        return (x - point) / (1-point) * alpha
    return x * alpha

# f1 = F(exp_opp, label = "f1(x)=x")
# f2 = F(dec, label = "f2(x)=x²")
#
#
# draw_ratio_function( f1, f2, f1+f2)


def rendement_aerobie(x,  mini=0.9):
    y = exp_opp_inv(x)
    if mini:
        y = y * (1-mini) + mini
    return y


def target_heart_rate(power, pma=200, fc_min=55, fc_max=187):
    intensity = power / (pma * 1.5)
    min_intensity = 0.3  # éviter log(0)
    adjusted_intensity = np.clip(intensity, min_intensity, 1)
    norm_log = np.log(adjusted_intensity / min_intensity) / np.log(1 / min_intensity)
    return fc_min + norm_log * (fc_max - fc_min)

if __name__ == "__main__":
    draw_ratio_function(
        exp_cb(opp=False, inv=True, steepness=10, label="0.3"),
        exp_cb(opp=True, steepness=1, label="1"),
        exp_cb(opp=True, steepness=10, label="10"),
    )
    #draw_function(power_serie(), target_heart_rate)