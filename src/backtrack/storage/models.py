import uuid
from datetime import datetime
from email.policy import default
from typing import Optional

from sqlmodel import SQLModel, Field

from xcb_sadel import Sadel


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


# class LogTrack(Sadel, table=True):
class LogTrack(SQLModel, table=True):
    # https://stackoverflow.com/questions/78054752/fastapi-sqlmodel-pydantic-not-serializing-datetime
    class Config:
        validate_assignment = True

    track_id: str = Field(default_factory=uuid.uuid4, primary_key=True)
    key: str = Field(default=None, primary_key=True)
    description: Optional[str] = Field(default=None)
    android_id: Optional[str] = Field(default=None)
    start_time: Optional[datetime] = Field(default=None)
    profile: Optional[str] = Field(default=None)

    # points: list["LogPoint"] = Relationship(back_populates="logpoint.track")

    @staticmethod
    def from_item(item: LogItem) -> "LogTrack":
        return LogTrack(track_id=item.track_id, key=item.key, description=item.description,
                        android_id=item.android_id,
                        start_time=item.start_time, profile=item.profile)


class LogPoint(SQLModel, table=True):
    # https://stackoverflow.com/questions/78054752/fastapi-sqlmodel-pydantic-not-serializing-datetime
    class Config:
        validate_assignment = True

    track_id: str = Field(default_factory=uuid.uuid4, primary_key=True, foreign_key="logtrack.track_id")
    ts: datetime = Field(default=None, primary_key=True)
    lat: float
    lon: float
    altitude: Optional[float] = Field(default=None)
    speed_kph: Optional[float] = Field(default=None)
    direction: Optional[float] = Field(default=None)
    distance: Optional[float] = Field(default=None)
    battery: Optional[float] = Field(default=None)
    accuracy: Optional[float] = Field(default=None)

    # track: list["LogPoint"] = Relationship(back_populates="logtrack.points")

    @staticmethod
    def from_item(item: LogItem) -> "LogPoint":
        return LogPoint(track_id=item.track_id, ts=item.ts, lat=item.lat, lon=item.lon,
                        altitude=item.altitude,
                        speed_kph=item.speed_kph, direction=item.direction, distance=item.distance,
                        battery=item.battery,
                        accuracy=item.accuracy)

