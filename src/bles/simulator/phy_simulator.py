import numpy as np

from bles.common.csv_elite import read_csv_elite
from bles.playground.functions import Line, show
from bles.simulator.base_simulator import PowerSimulator
from tests import TEST_DATA


class GPT2PowerSimulator(PowerSimulator):

    def __init__(self, fitness_level=0.7,
                 fat_utilization=0.6,
                carb_utilization = 0.9,
                glycogen_reserve = 100.0,
                fatigue = 0.5,
                 **kwargs):

        super().__init__(**kwargs)
        self.fc_min = self.min_freq
        self.fc_max = self.max_freq

        self.fitness_level = fitness_level
        self.fat_utilization = fat_utilization
        self.carb_utilization = carb_utilization
        self.glycogen_reserve = glycogen_reserve
        self.fatigue = fatigue


        # Simulation complète
        self.fc = [self.init_freq]
        self.glycogen = [self.glycogen_reserve]
        self.fatigue_series = [self.fatigue]

    def energy_source_ratio(self, power):
        intensity = power / self.pma
        fat_contrib = np.clip(1 - intensity * 1.8, 0, 1) * self.fat_utilization
        carb_contrib = np.clip(intensity * 1.2, 0, 1) * self.carb_utilization
        return fat_contrib, carb_contrib

    # Tau dynamique enrichi
    def compute_tau(self, fc, fat_contrib, carb_contrib, glycogen):
        base_tau = 20 - self.fitness_level * 10
        effort_penalty = 5 * (1 - fat_contrib) + 3 * carb_contrib
        glycogen_penalty = 5 if glycogen < 30 else 0
        fatigue_penalty = self.fatigue * 10
        return base_tau + effort_penalty + glycogen_penalty + fatigue_penalty

    # Cible FC
    def target_heart_rate(self, power):
        intensity = power / (self.pma * 1.25)
        min_intensity = 0.15  # éviter log(0)
        adjusted_intensity = np.clip(intensity, min_intensity, 1)
        norm_log = np.log(adjusted_intensity / min_intensity) / np.log(1 / min_intensity)
        return self.fc_min + norm_log * (self.fc_max - self.fc_min)

    def process(self, power):
        fat_contrib, carb_contrib = self.energy_source_ratio(power)

        glycogen_use = carb_contrib * power / self.pma * 0.5  # perte glycogène simplifiée
        glycogen_reserve = max(self.glycogen_reserve - glycogen_use, 0)

        self.fatigue += (power / self.pma) * 0.001 - 0.0003  # effort fatigue / récup réduit fatigue
        self.fatigue = np.clip(self.fatigue, 0, 1)

        fc_target = self.target_heart_rate(power)
        tau = self.compute_tau(self.fc[-1], fat_contrib, carb_contrib, glycogen_reserve)
        new_fc = self.fc[-1] + (fc_target - self.fc[-1]) / tau

        self.fc.append(new_fc)
        self.glycogen.append(glycogen_reserve)
        self.fatigue_series.append(self.fatigue)
        return new_fc

    def _step(self, target_power):
        return self.process(target_power)


def simulate(classe, csv, label=None, **kwargs):
    simu = classe(init_freq=csv[0]["heartrate"], **kwargs)
    ecart = 0
    ecart_moyen = 0
    ret = []
    for i, line in enumerate(csv):
        expected = line["heartrate"]
        power = line["power"]
        bpm = simu.step(power)


        ecart += abs(bpm - expected)
        ecart_moyen += bpm - expected

        ret.append(bpm)
    ecart /= len(csv)
    ecart_moyen /= len(csv)
    print(f"For {classe.__name__}({kwargs}) : {ecart:.3f} / {ecart_moyen:.3f}")
    if label:
        ret = Line(ret, label)
    return ret, ecart, ecart_moyen



def main():
    csv = read_csv_elite(TEST_DATA / "orca_share_media1747157600814_7328110113726402076.csv")
    real = Line([x["heartrate"] for x in csv], "real")
    T = [i for i in range(len(csv))]

    lines = []
    lines.append(simulate(GPT2PowerSimulator, csv, "GPT",
                                       fitness_level=0.3,
                                        fat_utilization = 0.6,
                                        carb_utilization = 0.9,
                                        glycogen_reserve = 0,
                                        fatigue = 0.0,
                                       )[0])

    lines.append(simulate(PowerSimulator, csv, "Manual")[0])

    show(T, real, *lines, Line([PowerSimulator.Z1*200 for _ in T])
         , Line([PowerSimulator.Z2*200 for _ in T]))
    #show(T, EX, FOUND, POW)


if __name__ == '__main__':
    main()
