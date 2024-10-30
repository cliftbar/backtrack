from enum import Enum


class TrackFormat(Enum):
    geojson = 'geojson'
    json = 'json'
    gpx = 'gpx'

    def content_type(self) -> str:
        if self == TrackFormat.geojson or self == TrackFormat.json:
            return 'application/json'
        elif self == TrackFormat.gpx:
            return 'application/xml'
