from pathlib import Path

from lxml import etree

from bles.common.tcx.model.biking import BikingActivity
from bles.common.tcx.model.running import RunningActivity


class TCX:

    _activities_ = {
        "Biking" : BikingActivity,
        "Running": RunningActivity
    }

    def __init__(self, root):
        self.activities = [self._activities_[x.attrib["Sport"]](x) for x in root.xpath(".//t:Activity", namespaces={"t": root.nsmap[None]})]


    @classmethod
    def from_file(cls, file):
        return cls(etree.fromstring(Path(file).read_bytes()))