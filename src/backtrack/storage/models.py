import uuid
from datetime import datetime, timezone
from typing import Optional, Any

import geojson
import lxml.etree as mod_etree
from geojson import LineString, Feature, FeatureCollection, Point
from gpxpy.gpx import GPX, GPXTrackPoint, GPXTrackSegment, GPXTrack, GPXWaypoint
from sqlmodel import SQLModel, Field, Column, DateTime

from backtrack.controllers.TrackFormat import TrackFormat
from backtrack.storage.encoders import DateTimeGeojsonEncoder


class LogItem(SQLModel, table=False):
    # https://stackoverflow.com/questions/78054752/fastapi-sqlmodel-pydantic-not-serializing-datetime
    class Config:
        validate_assignment = True

    key: str = Field(primary_key=True)
    track_id: str = Field(primary_key=True)
    ts: datetime = Field(primary_key=True)
    lat: float
    lon: float

    description: Optional[str] = Field(default=None)
    android_id: Optional[str] = Field(default=None)
    start_time: Optional[datetime] = Field(default=None)
    profile: Optional[str] = Field(default=None)

    altitude: Optional[float] = Field(default=None)
    speed_kph: Optional[float] = Field(default=None)
    direction: Optional[float] = Field(default=None)
    distance: Optional[float] = Field(default=None)
    battery: Optional[float] = Field(default=None)
    accuracy: Optional[float] = Field(default=None)


class LogTrackDetails(SQLModel, table=True):
    # https://stackoverflow.com/questions/78054752/fastapi-sqlmodel-pydantic-not-serializing-datetime
    class Config:
        validate_assignment = True

    track_id: str = Field(default_factory=uuid.uuid4, primary_key=True)
    key: str = Field(default=None, primary_key=True)
    description: Optional[str] = Field(default=None)
    android_id: Optional[str] = Field(default=None)
    start_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    profile: Optional[str] = Field(default=None)

    def start_time_tz(self) -> Optional[datetime]:
        return None if self.start_time is None else self.start_time.replace(tzinfo=timezone.utc)

    @staticmethod
    def from_item(item: LogItem) -> "LogTrackDetails":
        return LogTrackDetails(track_id=item.track_id, key=item.key, description=item.description,
                               android_id=item.android_id,
                               start_time=item.start_time, profile=item.profile)


class LogPoint(SQLModel, table=True):
    # https://stackoverflow.com/questions/78054752/fastapi-sqlmodel-pydantic-not-serializing-datetime
    class Config:
        validate_assignment = True

    track_id: str = Field(default_factory=uuid.uuid4, primary_key=True, foreign_key="logtrackdetails.track_id")
    ts: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=False, primary_key=True))
    lat: float
    lon: float
    altitude: Optional[float] = Field(default=None)
    speed_kph: Optional[float] = Field(default=None)
    direction: Optional[float] = Field(default=None)
    distance: Optional[float] = Field(default=None)
    battery: Optional[float] = Field(default=None)
    accuracy: Optional[float] = Field(default=None)

    def ts_tz(self) -> datetime:
        return self.ts.replace(tzinfo=timezone.utc)

    def xyz(self) -> tuple:
        ret = (self.lon, self.lat)
        if self.altitude is not None:
            ret = (self.lon, self.lat, self.altitude)
        return ret

    @staticmethod
    def from_item(item: LogItem) -> "LogPoint":
        return LogPoint(track_id=item.track_id, ts=item.ts, lat=item.lat, lon=item.lon,
                        altitude=item.altitude,
                        speed_kph=item.speed_kph, direction=item.direction, distance=item.distance,
                        battery=item.battery,
                        accuracy=item.accuracy)


class LogTrack(SQLModel, table=False):
    details: LogTrackDetails
    points: list[LogPoint]

    def get_geojson_track(self, first_point: bool = True) -> Optional[FeatureCollection]:

        point_set = [p.xyz() for p in self.points]
        line: LineString = LineString(point_set)
        l_feature = Feature(geometry=line, properties=self.details.model_dump())
        features: list[Feature] = [l_feature]
        if first_point:
            fp = self.points[0]
            point = Point(fp.xyz())
            props: dict[str, Any] = {
                "track_id": fp.track_id,
                "time": fp.ts_tz(),
            }
            if fp.speed_kph is not None:
                props["speed"] = fp.speed_kph
            if fp.direction is not None:
                props["direction"] = fp.direction
            if fp.distance is not None:
                props["distance"] = fp.distance
            if fp.battery is not None:
                props["battery"] = fp.battery
            if fp.accuracy is not None:
                props["accuracy"] = fp.accuracy

            p_feature: Feature = Feature(geometry=point, properties=props)
            features.append(p_feature)

        collection: FeatureCollection = FeatureCollection(features)
        return collection

    def get_gpx_track(self) -> Optional[GPX]:
        namespace = "backtrack"

        gpx = GPX()

        # Create first track in our GPX:
        gpx_track = GPXTrack(name=self.details.track_id)
        track_root: mod_etree.Element = mod_etree.Element(f"{namespace}")
        track_root.attrib["src"] = "backtrack"
        if self.details.start_time_tz() is not None:
            track_root.attrib["start_time"] = self.details.start_time_tz().isoformat(timespec='seconds')

        gpx_track.extensions.append(track_root)
        gpx.tracks.append(gpx_track)

        # Create Waypoint

        # Create first segment in our GPX track:
        gpx_segment = GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        for i, p in enumerate(self.points):
            gpx_point = GPXTrackPoint(latitude=p.lat, longitude=p.lon, elevation=p.altitude, time=p.ts_tz(),
                                      speed=p.speed_kph, name=p.track_id)
            point_root = mod_etree.Element(f'{namespace}')
            if p.speed_kph is not None:
                point_root.attrib["speed"] = str(p.speed_kph)
            if p.direction is not None:
                point_root.attrib["direction"] = str(p.direction)
            if p.distance is not None:
                point_root.attrib["distance"] = str(p.distance)
            if p.battery is not None:
                point_root.attrib["battery"] = str(p.battery)
            if p.accuracy is not None:
                point_root.attrib["accuracy"] = str(p.accuracy)

            gpx_point.extensions.append(point_root)
            gpx_segment.points.append(gpx_point)
            if i == 0:
                wpt = GPXWaypoint(latitude=p.lat, longitude=p.lon, elevation=p.altitude, time=p.ts_tz(),
                                  name=p.track_id,
                                  description="Latest Point")
                wpt.extensions.append(point_root)
                gpx.waypoints.append(wpt)

        return gpx

    def get_track_fmt_string(self, fmt: TrackFormat) -> str:
        if fmt == TrackFormat.geojson or fmt == TrackFormat.json:
            return geojson.dumps(self.get_geojson_track(), cls=DateTimeGeojsonEncoder)
        elif fmt == TrackFormat.gpx:
            return self.get_gpx_track().to_xml()
