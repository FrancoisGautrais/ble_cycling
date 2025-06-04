import asyncio
import os
import threading
import time
from queue import Queue

from bleak import BleakClient
from pycycling.fitness_machine_service import FitnessMachineService
from bles.ble import features
from dataclasses import dataclass

from pycycling.ftms_parsers import IndoorBikeData

from bles.ble.base import BaseBleClient, FeatureNotAvailable, SetValue, register_ble_client, BleClient


@dataclass
class CyclingData:
    power : int = 0
    resistance : int = 0
    speed : float = 0.0
    cadence : float = 0.0
    distance : float = 0
    timestamp : float = 0


    def copy(self, **kwargs):
        data = dict(self.__dict__)
        data.update(kwargs)
        return self.__class__(**data)


class SetResistance(SetValue):
    _field_ = "resistance"


class SetPower(SetValue):
    _field_ = "power"


class SetSimulationParam(SetValue):
    _field_ = "simulation"



@register_ble_client
class FitnessClient(BleClient):
    _data_class_ = CyclingData
    _feature_ = features.cycling

    def __init__(self, addresse, **other):
        super().__init__(addresse)
        self.ftms = FitnessMachineService(self._driver)
        self.ftms_features = None
        self.ftms_settings = None

    def _on_fitness_machine(self, data):
        pass

    def _on_indoor_bike_data(self, data : IndoorBikeData):
        self._set_data(
            speed=data.instant_speed,
            cadence = data.instant_cadence,
            distance = data.total_distance,
            resistance = data.resistance_level,
            power = data.instant_power
        )

    def _on_training_status(self, data):
        pass

    def _on_control_point_response(self, data):
        pass

    async def _start_service(self):
        self.start_time = time.time()
        self.ftms_features =(await self.ftms.get_fitness_machine_feature())._asdict()
        self.target_setting_features = (await self.ftms.get_target_setting_feature())._asdict()
        self.power_range = None
        self.resistance_range = None
        if self.target_setting_features["power_target_setting_supported"]:
            supported_power_range = await self.ftms.get_supported_power_range()
            self.power_range = [supported_power_range.minimum_power, supported_power_range.maximum_power]

        if self.target_setting_features["resistance_target_setting_supported"]:
            supported_resistance_level_range = await self.ftms.get_supported_resistance_level_range()
            self.resistance_range = [
                supported_resistance_level_range.minimum_resistance,
                supported_resistance_level_range.maximum_resistance
            ]
        self.ftms.set_training_status_handler(self._on_training_status)
        self.ftms.set_control_point_response_handler(self._on_control_point_response)
        self.ftms.set_fitness_machine_status_handler(self._on_fitness_machine)
        self.ftms.set_indoor_bike_data_handler(self._on_indoor_bike_data)
        await self.ftms.enable_training_status_notify()
        await self.ftms.enable_control_point_indicate()
        await self.ftms.enable_fitness_machine_status_notify()
        await self.ftms.enable_indoor_bike_data_notify()
        await self.ftms.request_control()
        await self.ftms.reset()

    async def _stop_services(self):
        await self.ftms.disable_training_status_notify()
        await self.ftms.disable_control_point_indicate()
        await self.ftms.disable_fitness_machine_status_notify()
        await self.ftms.disable_indoor_bike_data_notify()

    async def _set_target_resistance_abs(self, abs):
        abs = int(abs)
        if self.resistance_range is None:
            raise FeatureNotAvailable("resitance")

        if self.resistance_range[0] <= abs <= self.resistance_range[1]:
            await self.ftms.set_target_resistance_level(abs)
        else:
            raise ValueError(f"Resistance must be int in {self.resistance_range}")

    async def _set_simulation_params(self, w, g, cr, cw):
        await self.ftms.set_simulation_parameters(w, g, cr, cw)


    async def _set_target_resistance_rel(self, rel):
        if self.resistance_range is None:
            raise FeatureNotAvailable("resitance")
        if rel < 0 or rel>1:
            raise ValueError(f"Resistance must be float in [0,1]")

        v = (self.resistance_range[1]-self.resistance_range[0])*rel + self.resistance_range[0]
        await self.ftms.set_target_resistance_level(int(v))

    async def _set_target_power_abs(self, abs):
        abs = int(abs)
        if self.power_range is None:
            raise FeatureNotAvailable("power")

        if self.power_range[0] <= abs <= self.power_range[1]:
            await self.ftms.set_target_power(abs)
        else:
            raise ValueError(f"Power must be int in {self.power_range}")

    async def _set_target_power_rel(self, rel):
        if self.power_range is None:
            raise FeatureNotAvailable("power")
        if rel < 0 or rel>1:
            raise ValueError(f"Power must be float in [0,1]")
        v = (self.power_range[1]-self.power_range[0])*rel + self.power_range[0]

        await self.ftms.set_target_power(int(v))


    async def _on_message(self, next):
        v  = next.value
        if isinstance(next, SetPower):
            if isinstance(v, float):
                await self._set_target_power_rel(v)
            else:
                await self._set_target_power_abs(v)
        if isinstance(next, SetResistance):
            if isinstance(v, float):
                await self._set_target_resistance_rel(v)
            else:
                await self._set_target_resistance_abs(v)
        if isinstance(next, SetSimulationParam):
            await self._set_simulation_params(*v)

    def set_resistance(self, x):
        self._add_event(SetResistance(x))

    def set_power(self, x):
        self._add_event(SetPower(x))

    def set_simulation_param(self, wind, grad, crr, cw):
        self._add_event(SetSimulationParam((wind, grad, crr, cw)))


def main():
    os.environ["PYTHONASYNCIODEBUG"] = str(1)

    device_address = 'FB:6B:21:56:45:A7'
    client = FitnessClient(device_address)
    client.run_thread()
    client.join()

if __name__ == "__main__":
    main()