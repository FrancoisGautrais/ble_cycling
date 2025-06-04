from dataclasses import dataclass

from bles.ble_client.base import BaseData, BaseBleClient


@dataclass
class CyclingData(BaseData):
    power : int
    resistance : int
    timestamp : float


class CyclingBleClient(BaseBleClient):
    _feature_ = "cycling"
    _data_class_ : type = CyclingData

    def __init__(self):
        super().__init__()
        self.set_data(
            power=90,
            resistance=0
        )
