from datetime import datetime

from geojson import GeoJSONEncoder


class DateTimeGeojsonEncoder(GeoJSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat(timespec='seconds')
        return super().default(o)
