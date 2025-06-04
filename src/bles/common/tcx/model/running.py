import math

from bles.common.tcx.base.base import ModelBase, Container
from bles.common.tcx.base.fields import field


def distance(origin, destination):

    lat1, lon1 = origin.latitude, origin.longitude
    lat2, lon2 = destination.latitude, destination.longitude
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c * 1000

    return d

class  PointContainer(Container):

    def extend(self, it):
        for x in it:
            self.append(x)

    @property
    def last(self):
        return self[-1] if self else None

    def append(self, x):
        last = self.last
        if not last:
            x.distance = 0
        else:
            x.distance = last.distance + distance(last, x)

        return super().append(x)

    @property
    def speed_kmh(self):
        return sum(x.speed_kmh for x in self) / len(self)


class StatsMixin:
    container : PointContainer = None




class Point(ModelBase):
    time = field.DateTimeField(xpath=field.XpathStrictTagFinder("Time"))
    latitude = field.FloatField(xpath=field.XpathStrictTagFinder("Position", "LatitudeDegrees"))
    longitude = field.FloatField(xpath=field.XpathStrictTagFinder("Position", "LongitudeDegrees"))
    altitude = field.FloatField(xpath=field.XpathStrictTagFinder("AltitudeMeters"))
    bpm = field.FloatField(xpath=field.XpathStrictTagFinder("HeartRateBpm", "Value"))
    cadence = field.FloatField(xpath=field.XpathStrictTagFinder("Cadence"))
    speed_ms = field.FloatField(xpath=field.XpathStrictTagFinder("Extensions", "ns3:TPX", "ns3:Speed"))

    @property
    def speed_kmh(self):
        return self.speed_ms * 3.6

class Lap(ModelBase):
    total_time = field.FloatField(xpath=field.XpathTagFinder("TotalTimeSeconds"))
    distance = field.FloatField(xpath=field.XpathTagFinder("DistanceMeters"))
    calories = field.FloatField(xpath=field.XpathTagFinder("Calories"))
    average_bpm = field.FloatField(xpath=field.XpathTagFinder("AverageHeartRateBpm", "Value"))
    max_bpm = field.FloatField(xpath=field.XpathTagFinder("MaximumHeartRateBpm", "Value"))
    points = field.MultipleValueField(Point,
                                      container=PointContainer,
                                      xpath=field.XpathStrictTagFinder("Track", "Trackpoint"))



class RunningActivity(ModelBase):
    id = field.IdField()
    notes = field.NotesField()
    creator = field.CreatorField()
    laps = field.MultipleValueField(Lap, xpath=field.XpathStrictTagFinder("Lap"))


