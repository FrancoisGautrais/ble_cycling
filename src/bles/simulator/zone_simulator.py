
from functools import total_ordering

from bles.playground.functions import draw_function, show, Line


@total_ordering
class Unit:
    _type_ = None
    _name_ = None
    _allowed_unit_ = None

    def __init__(self, value):
        if isinstance(value, self.__class__):
            value = value.value
        elif isinstance(value, self._type_):
            pass
        else:
            raise TypeError()
        self.value = value

    def __repr__(self):
        return f"{self.value} {self._name_}"

    def __add__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(self.value + other.value)
        else:
            raise TypeError()

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.value < other.value
        else:
            raise TypeError()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        else:
            raise TypeError()



    def __iadd__(self, other):
        self.value = (self + other).value

    def __sub__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(self.value - other.value)
        else:
            raise TypeError()

    def __isub__(self, other):
        self.value = (self - other).value

    def __imul__(self, other):
        self.value = (self * other).value

    def __mul__(self, other):
        if isinstance(other, Ratio):
            return self.__class__(self.value * other.value)
        raise TypeError()

    def __itruediv__(self, other):
        self.value = (self / other).value

    def __truediv__(self, other):
        if isinstance(other, Ratio):
            return self.__class__(self.value * other.value)
        elif isinstance(other, self.__class__):
            return Ratio(self.value / other.value)
        raise TypeError()

    def __float__(self):
        return self.value

    def __int__(self):
        return int(self.value)

class FloatUnit(Unit):
    _type_ = (float, int)


class IntegerUnit(Unit):
    _type_ = int


class Ratio(FloatUnit):
    _name_ = ""


    def __mul__(self, other):
        o = other.value if isinstance(other, Unit) else float(other)
        return other.__class__(o * self.value)

    def __truediv__(self, other):
        o = other.value if isinstance(other, Unit) else float(other)
        return other.__class__(self.value / o)

    def __add__(self, other):
        o = other.value if isinstance(other, Unit) else float(other)
        return other.__class__(self.value + o)

    def __sub__(self, other):
        o = other.value if isinstance(other, Unit) else float(other)
        return other.__class__(self.value - o)


class Watt(FloatUnit):
    _name_ = "W"

    def __mul__(self, other):
        if isinstance(other, Ratio):
            return Watt(self.value * other.value)
        if isinstance(other, Second):
            return Joule(self, other)
        return super().__mul__(other)

class Second(IntegerUnit):
    _name_ = "s"

    def __mul__(self, other):
        if isinstance(other, Ratio):
            return Second(self.value * other.value)
        if isinstance(other, Watt):
            return Joule(other, self)
        return super().__mul__(other)

class Joule(FloatUnit):
    _name_ = "j"

    def __init__(self, w, s=None):
        if s is None:
            assert isinstance(w, (Joule, float))
            value = w
        else:
            assert isinstance(w, Watt)
            assert isinstance(s, Second)
            value = float(w.value * s.value)
        super().__init__(value)

    def __truediv__(self, other):
        if isinstance(other, Watt):
            return Second(self.value / other.value)
        if isinstance(other, Second):
            return Watt(self.value / other.value)
        return super().__truediv__(other)


class Zone:
    _capacity_ = None
    _debit_ = None
    _recharge_ = None
    _stress_ = 0


    def __init__(self, pma, age,  **kwargs):
        self.fc_min = 55
        self.fc_max = 187
        self.fc_range = self.fc_max - self.fc_min
        self.working_fc_ratio = [0, 0.7]

        self.kwargs = kwargs
        self.age = age
        self.pma = Watt(pma)
        self.capacity = Joule(self._get_capacity())
        self.capacity_max = Joule(self._get_capacity_max())
        self.debit_max = Watt(self._get_debit_max())
        self.recharge_max = Watt(self._get_recharge_max())
        self.stress = Ratio(self._get_stress())
        self.oxygen_demand = Ratio(0)


    def _get_capacity_max(self):
        assert self._capacity_ is not None
        return self.pma * Second(self._capacity_)

    def _get_stress(self):
        return self._stress_

    def _get_capacity(self):
        assert self._capacity_ is not None
        return self.pma * Second(self._capacity_)

    def _get_debit_max(self):
        assert self._debit_ is not None
        return self.pma * Ratio(self._debit_)

    def _get_recharge_max(self):
        return 0

    @property
    def debit(self) -> Watt:
        return self.debit_max


    def require_power(self, power : Watt):
        energy = power * Second(1)
        primary_energy = energy * (Ratio(1) + self.stress * Ratio(0.1))

        maxi = min(self.capacity, self.debit*Second(1))
        xb = min(maxi, primary_energy)
        self._require_power(xb / maxi)

        ret = max(Joule(0.0), primary_energy-maxi)
        return ret


    def _require_power(self, x):
        raise NotImplementedError()

    @property
    def bpm(self):
        r = self.working_fc_ratio[1] - self.working_fc_ratio[0]
        return float(self.oxygen_demand) * r * self.fc_range


class ZoneAerobie(Zone):
    _capacity_ = 3600 * 4
    _debit_ = 0.7

    @property
    def debit(self):
        return self.debit_max


    def _require_power(self, x : Ratio):
        self.oxygen_demand = float(x)
        self.stress = Ratio((self.stress * 9.0 + self.oxygen_demand) / 10.0)


def power_curve(*args):
    ret = []
    for w, t in args:
        ret.extend([w for _ in range(t)])
    return ret


if __name__ == "__main__":
    MIN = 60
    curve = power_curve(
            (200, 3 * MIN),
            (100, 3 * MIN),
            (120, 3 * MIN),
            (150, 3 * MIN),
            (200, 6 * MIN),
            (150, 3 * MIN),
            (220, 6 * MIN),
            (180, 3 * MIN),
            (150, 3 * MIN),
            (120, 3 * MIN),
            (100, 3 * MIN),
    )

    z = ZoneAerobie(200, 33)
    POW = Line(curve, "power")
    REALPOW = Line([], "real_power")
    STRESS = Line([], "stress")
    TIME = []
    Y = Line([], "bpm")
    for i, x in enumerate(POW):
        TIME.append(i)
        REALPOW.append(x-float(z.require_power(Watt(x))))
        bpm = z.bpm+ 55
        Y.append(bpm)
        STRESS.append(z.stress*100)

    show(TIME, POW, Y, REALPOW, STRESS)
