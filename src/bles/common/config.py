



import configparser
import json
from pathlib import Path


import os


def deep_update(mapping, *updating_mappings):
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping



class SequencerConfig:

    def __init__(self):
        self._data = {
            "devices" : {

            },
            "ble_clients" : {

            },
            "controllers" : {

            },
            "period" : 1
        }

    def to_json(self):
        return self._data

    def load_json(self, data):
        self._data = data

    def load_file(self, file):
        self._data = json.loads(Path(file).read_text())

    @property
    def devices(self):
        return self._data["devices"]

    @property
    def controllers(self):
        return self._data["controllers"]

    @property
    def ble_clients(self):
        return self._data["ble_clients"]


    def add_controller(self, name, params=None, **kwargs):
        kwargs.update(params or {})
        self._data["controllers"][name] = {
            "name" : name,
            "params" : kwargs
        }

    def add_ble_client(self, device_name, feature, params=None, **kwargs):
        kwargs.update(params or {})

        self._data["ble_clients"][feature] = {
            "feature": feature,
            "params": kwargs,
            "device": device_name
        }

    def add_device(self, name, address):
        self._data["devices"][name] = address

    @property
    def period(self):
        return  self._data["period"]

    @period.setter
    def period(self, x):
        self._data["period"] = x



class Config:


    _files_ = [
        Path.home() / ".config/ble_cycling/config.json",
        "ble_cycling.json",
        "/etc/ble_cycling.json",
    ]

    _default_ = {
        "app" : {
            "host" : "0.0.0.0",
            "port" : 8000,
            "data_dir" :  str(Path.home() / ".config/ble_cycling")
        },
        "sequencer" : {
              "devices": {
                "cycling": "FB:6B:21:56:45:A7",
                "heart_rate": "D2:60:F3:44:A7:07"
              },
              "ble_clients": {
                "heart_rate": {
                  "feature": "heart_rate",
                  "params": {

                  },
                  "device": "heart_rate"
                },
                "cycling": {
                  "feature": "cycling",
                  "params": {

                  },
                  "device": "cycling"
                }
              },
              "controllers": {
                "power": {
                  "name": "power",
                  "params": {

                  }
                },
                "resistance": {
                  "name": "resistance",
                  "params": {

                  }
                },
                "simulation": {
                  "name": "simulation",
                  "params": {

                  }
                },
                "heart_rate": {
                  "name": "heart_rate",
                  "params": {

                  }
                }
              },
              "period": 1
        },
        "stats" : {

        }
    }

    def __init__(self):
        self._data = {}
        self.reload()


    def reload(self):
        self._data = {}
        self._data = deep_update(self._data , self._default_)
        for file in self._files_:
            file = Path(file)
            if file.is_file():
                try:
                    self.load_file(file)
                except:
                    continue
                break



    def load(self, data):
        self._data = {}
        self._data = deep_update(self._data ,data)

    def load_file(self, file):
        data = json.loads(Path(file).read_text())
        self.load(data)
        self._file = Path(self._file)

    def save(self, file=None):
        file = Path(file or self._file)
        self._file = file
        self._file.parent.mkdir(exist_ok=True, parents=True)

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value

    @property
    def app_data_dir(self):
        return Path(self["app"]["data_dir"])

    @property
    def app_host(self):
        return self._data["app"]["host"]

    @property
    def app_port(self):
        return self._data["app"]["port"]

    @property
    def sequencer(self):
        tmp = SequencerConfig()
        tmp.load_json(self["sequencer"])
        return tmp


config = Config()


