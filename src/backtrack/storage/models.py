import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field

from xcb_sadel import Sadel


class LogItem(SQLModel, table=False):
    # https://stackoverflow.com/questions/78054752/fastapi-sqlmodel-pydantic-not-serializing-datetime
    class Config:
        validate_assignment = True

    key: str
    description: str
    android_id: str
    start_time: datetime
    profile: str
    filename: str

    ts: datetime
    lat: float
    lon: float
    altitude: float
    speed_kph: float
    direction: float
    distance: float
    battery: float
    accuracy: float

    def default_track_id(self) -> str:
        # return f"{self.key}_{self.start_time.strftime('%Y-%m-%dT%H-%M-%S')}"

        return f"{self.filename}"


# class LogTrack(Sadel, table=True):
class LogTrack(SQLModel, table=True):
    # _upsert_index_elements = {"track_id", "key"}
    # _upsert_exclude_fields = {"track_id", "key", "android_id", "start_time", "filename", "profile"}

    # https://stackoverflow.com/questions/78054752/fastapi-sqlmodel-pydantic-not-serializing-datetime
    class Config:
        validate_assignment = True

    track_id: str = Field(default_factory=uuid.uuid4, primary_key=True)
    key: str = Field(default=None, primary_key=True)
    description: str
    android_id: str
    start_time: datetime
    profile: str
    filename: str

    # points: list["LogPoint"] = Relationship(back_populates="logpoint.track")

    @staticmethod
    def from_item(item: LogItem) -> "LogTrack":
        return LogTrack(track_id=item.default_track_id(), key=item.key, description=item.description,
                        android_id=item.android_id,
                        start_time=item.start_time, profile=item.profile, filename=item.filename)


class LogPoint(SQLModel, table=True):
    # https://stackoverflow.com/questions/78054752/fastapi-sqlmodel-pydantic-not-serializing-datetime
    class Config:
        validate_assignment = True

    track_id: str = Field(default_factory=uuid.uuid4, primary_key=True, foreign_key="logtrack.track_id")
    ts: datetime = Field(default=None, primary_key=True)
    lat: float
    lon: float
    altitude: float
    speed_kph: float
    direction: float
    distance: float
    battery: float
    accuracy: float

    # track: list["LogPoint"] = Relationship(back_populates="logtrack.points")

    @staticmethod
    def from_item(item: LogItem) -> "LogPoint":
        return LogPoint(track_id=item.default_track_id(), ts=item.ts, lat=item.lat, lon=item.lon,
                        altitude=item.altitude,
                        speed_kph=item.speed_kph, direction=item.direction, distance=item.distance,
                        battery=item.battery,
                        accuracy=item.accuracy)

