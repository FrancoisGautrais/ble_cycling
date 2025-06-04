import os
import time
from dataclasses import dataclass

from pycycling.heart_rate_service import HeartRateService
from bles.ble import features
from bles.ble.base import register_ble_client, BleClient


@dataclass
class HRSState:
    bpm : int = 0
    timestamp : float = 0


    def copy(self, **kwargs):
        data = dict(self.__dict__)
        data.update(kwargs)
        return self.__class__(**data)

@register_ble_client
class HeartClient(BleClient):
    _feature_ = features.heart_rate
    _data_class_ = HRSState

    def __init__(self, addresse, **other):
        super().__init__(addresse)
        self.start_time = time.time()
        self.hrs : HeartRateService = None

    def _on_data(self, data):
        self._set_data(bpm=data.bpm)

    async def _start_service(self):
        self.hrs = HeartRateService(self._driver)
        self.hrs.set_hr_measurement_handler(self._on_data)
        await self.hrs.enable_hr_measurement_notifications()

    async def _stop_services(self):
        await self.hrs.disable_hr_measurement_notifications()

    async def _on_message(self, next):
        pass

def main():
    os.environ["PYTHONASYNCIODEBUG"] = str(1)

    device_address = 'D2:60:F3:44:A7:07'
    client = HeartClient(device_address)
    client.run_thread()
    client.join()

if __name__ == "__main__":
    main()