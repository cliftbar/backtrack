from datetime import datetime, timezone
from random import Random
from typing import Optional

from sqids import Sqids
from sqlalchemy import Engine
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlmodel import select, Session

from backtrack.storage.models import LogTrackDetails, LogPoint, LogTrack


class BacktrackController:
    def __init__(self, engine: Engine, async_engine: AsyncEngine):
        self.async_engine = async_engine
        self.engine = engine
        self.sqids = Sqids(min_length=5)
        self.rand = Random()

    async def store_log(self, track: LogTrackDetails, point: LogPoint) -> None:
        async with (AsyncSession(self.async_engine) as session):
            statement = insert(track.__class__).values(**track.model_dump(exclude_unset=True)).on_conflict_do_nothing()
            await session.execute(statement)
            # session.add(track)
            session.add(point)
            await session.commit()

    def get_track(self, key: str, track_id: str) -> Optional[LogTrack]:
        with Session(self.engine) as session:
            stmt = select(LogTrackDetails).where(LogTrackDetails.key == key).where(LogTrackDetails.track_id == track_id)
            track = list(session.exec(stmt))
            if track is None or len(track) == 0:
                return None
            points: list[LogPoint] = list(
                session.exec(select(LogPoint).where(LogPoint.track_id == track_id).order_by(LogPoint.ts.desc())))

        return LogTrack(details=track[0], points=points)

    async def get_next_squid(self) -> str:
        with Session(self.engine) as session:
            with session.begin():
                tracks: list[LogTrackDetails] = list(session.exec(select(LogTrackDetails)))
                keys: set[str] = set([t.key for t in tracks])
                while True:
                    new_key: str = self.sqids.encode(
                        [int(datetime.now(tz=timezone.utc).timestamp()), self.rand.randint(0, 1000)])
                    if new_key not in keys:
                        break

        return new_key

    async def get_tracks(self, key) -> list[LogTrackDetails]:
        with Session(self.engine) as session:
            tracks: list[LogTrackDetails] = list(
                session.exec(select(LogTrackDetails).where(LogTrackDetails.key == key)))

        return tracks

    async def get_user_tracks(self, key: str) -> list[str]:
        async with Session(self.engine) as session:
            tracks: list[LogTrackDetails] = list(
                session.exec(select(LogTrackDetails).where(LogTrackDetails.key == key)))

        return [track.track_id for track in tracks]

    @staticmethod
    def make_profile(key: str, track_id: str) -> str:
        profile: dict[str, str] = {
            "log_customurl_method": "POST",
            "log_customurl_body": '{{"key"\: "{key}","track_id"\: "%FILENAME","description"\: "%DESC","ts"\: "%TIME","lat"\: %LAT,"lon"\: %LON,"altitude"\: %ALT,"direction"\: %DIR,"speed_kph"\: %SPD_KPH,"distance"\: %DIST,"battery"\: %BATT,"accuracy"\: %ACC,"android_id"\: "%AID","start_time"\: %STARTTIMESTAMP,"profile"\: "%PROFILE"}}',
            "current_profile_name": "{name}",
            "log_customurl_url": "https\://backtrack.cliftbar.site/track",
            "log_customurl_discard_offline_locations_enabled": "false",
            "accuracy_before_logging": "40",
            "new_file_creation": "custom",
            "log_plain_text": "true",
            "log_plain_text_csv_delimiter": ",",
            "hide_notification_buttons": "false",
            "log_customurl_enabled": "true",
            "distance_before_logging": "0",
            "log_satellite_locations": "true",
            "log_network_locations": "true",
            "new_file_custom_name": "{name}",
            "new_file_custom_each_time": "true"
        }

        profile["current_profile_name"] = profile["current_profile_name"].format(name=key)
        profile["new_file_custom_name"] = profile["new_file_custom_name"].format(name=track_id)
        profile["log_customurl_body"] = profile["log_customurl_body"].format(key=key)

        profile_text: str = ""
        for k, v in profile.items():
            profile_text += f"{k}={v}\n"
        return profile_text
