import datetime
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from bles.common.config import config

DEFAULT_HR = {
    "bpm" : 0
}

DEFAULT_CYLCING = {
    "power" : 0,
    "resistance" : 0,
    "speed" : 0,
    "cadence" : 0.0,
    "distance" : 0,
}

@dataclass
class Point:

    timestamp : float = 0
    bpm : int = None
    power: int = None
    resistance: int = None
    speed: float = None
    cadence: float = None
    distance: float = 0

    @classmethod
    def new(cls, data):
        cy = data.get("cycling", DEFAULT_CYLCING)
        hr = data.get("heart_rate", DEFAULT_HR)
        tmp = dict(cy)
        tmp.update(hr)
        tmp["timestamp"] = time.time()
        return cls(
            **tmp
        )




class Stat:
    _dataclass_ = Point


    _instant_variable_ = [
        "bpm",
        "power",
        "resistance",
        "speed",
        "cadence",
    ]



    def __init__(self):
        d = datetime.datetime.now()
        name = d.strftime("%Y%m%d_%H%M%S")
        self._fields = list(self._dataclass_.__dataclass_fields__)
        self.root_dir =  config.app_data_dir / "data" / name
        self.root_dir.mkdir(exist_ok=True, parents=True)
        self.csv_fd = open(self.root_dir / "data.csv", "w")
        self.data = []
        self.last = None
        self.count = Point(**{k: 0 for k in self._instant_variable_})
        self.avg = Point(**{k: 0 for k in self._instant_variable_})
        self.max = Point(**{k: 0 for k in self._instant_variable_})
        self.min = Point(**{k: 0 for k in self._instant_variable_})

        self.csv_fd.write(";".join(self._fields)+"\n")

    def get_state(self):
        return {
            "count": self.count,
            "avg": self.avg,
            "max": self.max,
            "min": self.min,
            "last": self.last,
        }

    def _create_point(self, data):
        return self._dataclass_.new(data)

    def close(self):
        self.csv_fd.close()

    def append(self, data):
        ret = self._create_point(data)
        self.data.append(ret)
        self.last = ret
        for k in self._instant_variable_:
            v = getattr(ret, k)
            if v is None:
                setattr(ret, k, 0)
            else:
                count = getattr(self.count, k)
                setattr(self.count, k, count+1)
                setattr(self.avg, k, (getattr(self.avg, k)*count + v) / (count +1 ))
                setattr(self.min, k, min(getattr(self.min, k), v))
                setattr(self.max, k, max(getattr(self.max, k), v))

        try:
            self.csv_fd.write(";".join([str(getattr(self.last, x)) for x in self._fields])+"\n")
            self.csv_fd.flush()
        except ValueError:
            pass

        return ret

    def as_panda(self):
        return pd.DataFrame(self.data)

    def write_csv(self, path_or_buff, **kwargs):
        p = self.as_panda()
        kwargs.setdefault("sep", ";")
        if isinstance(path_or_buff, (str, Path)):
            Path(path_or_buff).parent.mkdir(exist_ok=True, parents=True)
        p.to_csv(path_or_buff, **kwargs)