from dataclasses import dataclass

from bles.ble_client.base import BaseBleClient, BaseData


@dataclass
class HeartRateData(BaseData):
    bpm : int
    timestamp : float


class HRBleClient(BaseBleClient):
    _data_class_ : type = HeartRateData
    _feature_ = "hear_rate"

    def __init__(self, adresse):
        super().__init__(adresse)
        self.set_data(bpm=93)