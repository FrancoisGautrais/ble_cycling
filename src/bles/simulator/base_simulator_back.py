import math
import random
from collections import namedtuple

import numpy as np
from matplotlib import pyplot as plt

from bles.common.csv_elite import read_csv_elite
from tests import TEST_DATA


def show(X, *Yn):
    fig, ax = plt.subplots()  # Create a figure containing a single Axes.
    for Y in Yn:
        print("printed")
        ax.plot(X, Y)  # Plot some data on the Axes.
    plt.show()


def f(x):
    k = 100
    base = 10
    x = min(max(x, 0), 1)
    ret =  math.log(1+( k-x*k), base) / math.log(1+k, base)
    return  ret


def fb(x):
    k = 1
    base = 2
    x = min(max(x, 0), 1)
    ret =  math.log(1+(x*k), base) / math.log(1+k, base)
    return  x

def f2(x):
    k = 100
    base = 2
    x = min(max(x, 0), 1)
    ret = math.log(1+( x*k), base) / math.log(1+k, base)
    return  ret

def f2b(x):
    k = 0.05
    base = 2
    x = min(max(x, 0), 1)
    ret = 1 - math.log(1+( x*k), base) / math.log(1+k, base)
    return  1-x



def _test(f):
    X = [ i / 100 for i in range(100)]
    Y = [f(x) for x in X ]
    show(X, Y)
    exit(0)


def _test2(f):
    med = 90
    X = [ (i+55)  for i in range(133)]
    Y = [f( abs(x-med) / 66) for x in X ]
    show(X, Y)
    exit(0)

def f3(x):

    k = 1000
    base = 2
    x = min(max(x, 0), 1)
    ret = math.log(1+( k - x*k), base) / math.log(1+k, base)
    return ret

def _test3(f):
    med = 90
    X = [ (i/100)  for i in range(101)]
    Y = [f(x) for x in X ]
    show(X, Y)
    exit(0)


class BaseSimulator:
    pass


class Zone:
    def __init__(self, name, capacite, debit_max, recharge):
        self.name = name
        self.capacite_max = capacite
        self.capacite = capacite
        self.debit_max = debit_max
        self.recharge = recharge
        self.last = None


    def recup(self, x):
        rec = self.recharge * x
        self.capacite = min(self.capacite + rec, self.capacite_max)


    def effort(self, x):
        return fb(x)

    def consume(self, x):
        maxi = min(self.capacite, self.debit_max)
        if x > maxi:
            ret =  x - maxi
            self.capacite -= maxi
            return  ret, self.effort(1)

        self.capacite -= x
        self.last = self.effort(x / maxi)

        return 0, self.last

    @property
    def left(self):
        return self.capacite / self.capacite_max



class PowerSimulator(BaseSimulator):
    Z1 = 0.7
    Z2 = 0.85
    Result = namedtuple("Result", ["bpm", "power"])

    def __init__(self, min_freq = 55, max_freq=187, pma=200,
                 init_freq=None):
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.pma = pma
        self.time = 0
        self.range_fc = self.max_freq - self.min_freq
        self.init_freq = init_freq

        self._z1 = Zone("z1", self.pma * 3600 * 0.6, self.pma * 0.6, self.pma)
        self._z2 = Zone("z2", self.pma * 3600 * 0.2, self.pma, self.pma * 0.5)
        self._z3 = Zone("z3", self.pma * 3600 * 0.1, self.pma * 100, self.pma)




        self._bpms = []
        self._effective_power = []
        self._target_power = []
        self._effort_charge = []



    def _effort_calc(self, effective_power):
        pc = effective_power / self.pma
        return pc




    def effort_to_bpm(self, last_bpm, effective_power):
        pc = effective_power / self.pma
        z1 = min(1, pc / self.Z1)
        z2 = 0
        if z1 > 0.95:
            z2 = min(1, pc / self.Z2)
        if z2>0.95:
            z3 = min(1, pc )



        target = pc * self.range_fc + self.min_freq


        return last_bpm + target / 100

    @property
    def last_bpm(self):
        last_bpm = None
        if self._bpms:
            last_bpm = self._bpms[-1]
        else:
            if not self.init_freq:
                base = random.randint(14, 40) / 100
                self.init_freq = int(self.min_freq + base * self.range_fc)
            last_bpm = self.init_freq
        return last_bpm

    def _step(self, target_power):
        self._target_power.append(target_power)

        effective_power = target_power
        z1_left, eff1 = self._z1.consume(effective_power)
        z2_left, eff2 = self._z2.consume(z1_left)
        z3_left, eff3 = self._z3.consume(z2_left)

        if z3_left:
            effective_power -= z3_left

        recup =  1 - eff1
        if recup > 0:
            self._z1.recup(recup)
            self._z2.recup(recup)
            self._z2.recup(recup)

        target_bpm = eff1  * 0.7 * self.pma
        if eff2:
            target_bpm += eff2*0.38 * self.pma
        if eff3:
            target_bpm += eff3*0.3 * self.pma

        last_bpm = self.last_bpm

        diff = (target_bpm - last_bpm)
        diff_rel = abs(diff) / self.range_fc



        med = 100

        if diff > 0:
            ecart_rel = f(diff_rel)
            rapport = 2
            ecart_med =  f2( abs(last_bpm - med) / (self.range_fc/2) ) / rapport +  1 - (1/rapport)
        else:
            ecart_rel = f(diff_rel)*0.9
            rapport = 7
            ecart_med =  f2b( abs(last_bpm - med) / (self.range_fc/2) ) / rapport +  1 - (1/rapport)
        delta = diff / (1 + ecart_rel * ecart_med  * 100)


        bpm = last_bpm + delta
        self._bpms.append(bpm)


        return bpm





    def step(self, target_power, times=1):
        ret = None
        for _ in range(int(times)):
            self.time += 1
            ret = self._step(target_power)
        return ret




def main():
    csv = read_csv_elite(TEST_DATA / "orca_share_media1747157600814_7328110113726402076.csv")
    simu = PowerSimulator(init_freq=csv[0]["heartrate"])
    ecart = 0

    EX = []
    FOUND = []
    POW = []
    T = []

    for i, line in enumerate(csv):
        expected = line["heartrate"]
        power = line["power"]
        bpm = simu.step(power)


        ecart += abs(bpm - expected)

        EX.append(expected)
        FOUND.append(bpm)
        POW.append(power)
        T.append(i)

        zones = [simu._z1, simu._z2, simu._z3]
        print(f"[{simu.time}] power={power} bpm={int(bpm)} / {expected}  : effort={[int(x.last*100)/100 for x in zones]} res={[int(x.left*100)/100 for x in zones]}")

    print(f"Total : {int(ecart)} ( {(ecart/len(csv))})")

    Z1 = [simu.pma * 0.7 for _ in T]
    Z2 = [simu.pma * 0.9 for _ in T]
    show(T, EX, FOUND, Z1, Z2)
    #show(T, EX, FOUND, POW)


if __name__ == '__main__':
    main()
