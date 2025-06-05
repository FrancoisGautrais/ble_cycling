import math
import random
from collections import namedtuple

import numpy as np
from matplotlib import pyplot as plt

from bles.common.csv_elite import read_csv_elite
from bles.playground import functions
from bles.playground.functions import exp_cb
from tests import TEST_DATA

def show(X, *Yn):
    fig, ax = plt.subplots()  # Create a figure containing a single Axes.
    for Y in Yn:
        ax.plot(X, Y)  # Plot some data on the Axes.
    plt.show()


def f(x, k=100, base=10):
    x = np.clip(x, 0,1)
    ret =  math.log(1+( k-x*k), base) / math.log(1+k, base)
    return  ret


def fb(x, k=1, base=2):
    x = np.clip(x, 0,1)
    ret =  math.log(1+(x*k), base) / math.log(1+k, base)
    return  ret

def f2(x, k=100, base=2):
    x = np.clip(x, 0,1)
    ret = math.log(1+( x*k), base) / math.log(1+k, base)
    return  ret

def f2b(x, k=0.05, base=2):
    x = np.clip(x, 0,1)
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
    bpm_ratio_working = []
    def __init__(self, fc_min, fc_max, capacite, debit_max, recharge):
        self.capacite_max = capacite
        self.capacite = capacite
        self.debit_max = debit_max
        self.recharge = recharge
        self.last = None
        self.last_effort = 0

        self.fc_range = fc_max - fc_min
        self.fc_min = self.bpm_ratio_working[0] * self.fc_range + fc_min
        self.fc_max = self.bpm_ratio_working[1] * self.fc_range + fc_min
        self.zone_fc_range = self.fc_max - self.fc_min


    def recup(self, x):
        rec = self.recharge * x
        self.capacite = min(self.capacite + rec, self.capacite_max)


    def effort(self, x):
        raise NotImplementedError()

    def effort_to_bpm(self, x):
        eff = self.effort(x)
        return eff * self.zone_fc_range

    def consume(self, x):
        K = 0
        maxi = min(self.capacite, self.debit_max)
        ret =  max(0, x - maxi)
        x = min(x, maxi)

        self.capacite -= x
        maxi = max(maxi, 1)

        tmp = (self.last_effort * K + x / maxi) / (K+1)


        self.last = self.effort_to_bpm(tmp)
        self.last_effort = tmp

        return ret, self.last

    @property
    def left(self):
        return self.capacite / self.capacite_max


class Zone1(Zone):
    bpm_ratio_working = [0, 0.7] #[0.5, 0.7]
    def effort(self, x):
        x = max(x, 0.5)
        return x # functions.exp_opp(x)

class Zone2(Zone):
    bpm_ratio_working = [0.68, 0.9]
    def effort(self, x):
        return x

class Zone3(Zone):
    bpm_ratio_working = [0.88, 1]
    def effort(self, x):
        return x



class PowerSimulator(BaseSimulator):
    Z1 = 0.7
    Z2 = 0.85
    Result = namedtuple("Result", ["bpm", "power"])

    def __init__(self, min_freq = 55, max_freq=187, pma=200,
                 init_freq=None):
        self.min_freq = min_freq
        self._time = 0
        self.max_freq = max_freq
        self.pma = pma
        self.time = 0
        self.range_fc = self.max_freq - self.min_freq
        self.init_freq = init_freq

        self._z1 = Zone1(self.min_freq, self.max_freq, self.pma * 3600 * 0.6, self.pma * 0.6, self.pma)
        self._z2 = Zone2(self.min_freq, self.max_freq, self.pma * 3600 * 0.2, self.pma, self.pma * 0.5)
        self._z3 = Zone3(self.min_freq, self.max_freq, self.pma * 3600 * 0.1, self.pma * 100, self.pma)




        self._bpms = []
        self._effective_power = []
        self._target_power = []
        self._effort_charge = []




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
        self._time += 1
        effective_power = target_power
        z1_left, bpm1 = self._z1.consume(effective_power)
        z2_left, bpm2 = self._z2.consume(z1_left)
        z3_left, bpm3 = self._z3.consume(z2_left)

        if z3_left:
            effective_power -= z3_left

        # recup =  1 - eff1
        # if recup > 0:
        #     self._z1.recup(recup)
        #     self._z2.recup(recup)
        #     self._z2.recup(recup)

        target_bpm = self.min_freq + bpm3 + bpm1 + bpm2
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
            self._target_power.append(target_power)
            ret = self._step(target_power)
        return ret



class GPTPowerSimulator(PowerSimulator):

    def tau_dynamic(self, fc):
        """
        Tau varie de manière exponentielle avec la FC.
        Plus on approche FC_max, plus tau est petit.
        """
        tau_rest = 30
        tau_peak = 5

        ratio = (fc - self.min_freq) / self.range_fc
        return tau_peak + (tau_rest - tau_peak) * np.exp(-4 * ratio)

    def target_heart_rate(self, power):
        """Fréquence cardiaque cible à un instant donné, en fonction de la puissance"""
        power_ratio = power / self.pma
        steepness = 4.1
        midpoint = 0.5
        return self.min_freq + (self.max_freq - self.min_freq) / (1 + np.exp(-steepness * (power_ratio - midpoint)))

    def simulate_dynamic_heart_rate(self, power_series):
        """
        Simule l'évolution dynamique de la fréquence cardiaque au fil du temps.

        :param power_series: tableau de puissance à chaque seconde (en W)
        :param fc_min: FC minimale
        :param fc_max: FC maximale
        :param pma: Puissance maximale aérobie
        :param initial_fc: FC initiale au début de la simulation
        :param tau: constante de temps (plus petit = adaptation plus rapide)
        :return: tableau des fréquences cardiaques simulées
        """
        fc_values = np.zeros(len(power_series))
        fc_values[0] = self.init_freq or 100

        tau = self.tau_dynamic(fc_values[-1])

        for t in range(1, len(power_series)):
            fc_target = self.target_heart_rate(power_series[t])
            # Formule d'ajustement exponentiel
            fc_values[t] = fc_values[t - 1] + (fc_target - fc_values[t - 1]) / tau

        return fc_values

    def _step(self, target_power):
        real_power = int(target_power)
        self._target_power.append(real_power)
        powers = np.array(self._target_power, dtype=int)
        ret = self.simulate_dynamic_heart_rate(powers)
        bpm = ret[-1]
        self._bpms.append(bpm)
        return bpm


def get_values():
    csv = read_csv_elite(TEST_DATA / "orca_share_media1747157600814_7328110113726402076.csv")
    simu = GPTPowerSimulator(init_freq=csv[0]["heartrate"])
    powers = np.array([x["power"] for x in csv], dtype=int)
    hrs = np.array([x["heartrate"] for x in csv], dtype=int)
    bpms = simu.simulate_dynamic_heart_rate(powers)
    error = 0
    for found, expected in zip(bpms, hrs):
        error += abs(found - expected)
    error /= len(bpms)
    return bpms, error


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

        #zones = [simu._z1, simu._z2, simu._z3]
        #print(f"[{simu.time}] power={power} bpm={int(bpm)} / {expected}  : effort={[int(x.last*100)/100 for x in zones]} res={[int(x.left*100)/100 for x in zones]}")
        #print(f"[{simu.time}] power={power} bpm={int(bpm)} / {expected}")


    Z1 = [simu.pma * 0.7 for _ in T]
    Z2 = [simu.pma * 0.9 for _ in T]

    gpt_bpms, gpt_error = get_values()
    print(f"Total : ( {(ecart/len(csv))}) GPT={gpt_error}")

    show(T, EX, FOUND, gpt_bpms, Z1, Z2)
    #show(T, EX, FOUND, POW)


if __name__ == '__main__':
    main()
