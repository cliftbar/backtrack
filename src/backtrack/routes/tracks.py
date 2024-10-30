from typing import Optional

from fastapi import Request, HTTPException, APIRouter
from starlette.responses import Response

from backtrack.controllers import controller
from backtrack.controllers.TrackFormat import TrackFormat
from backtrack.storage.models import LogTrackDetails, LogItem, LogPoint, LogTrack

tracks_router: APIRouter = APIRouter()


@tracks_router.post("/log")
async def print_log(request: Request):
    body_text: str = (await request.body()).decode("utf-8")
    print(body_text)


@tracks_router.post("/track")
async def store_log(log_item: LogItem):
    # print(log_item)
    track: LogTrackDetails = LogTrackDetails.from_item(log_item)
    point: LogPoint = LogPoint.from_item(log_item)
    # print(track)
    # print(point)

    await controller.store_log(track, point)  # print(f"point for {log_item.default_track_id()} saved")


@tracks_router.get("/tracks")
async def get_tracks(key: str):
    tracks = await controller.get_tracks(key)
    if not tracks:
        raise HTTPException(status_code=404, detail=f"{key} not found")
    return [t.track_id for t in tracks]


@tracks_router.get("/track")
async def get_track_query(key: str, track_id: str, fmt: str = "json"):
    return await get_track(key, track_id, fmt)


@tracks_router.get("/{key}/track/{track_id}/{fmt}")
async def get_track_path(key: str, track_id: str, fmt: str) -> Response:
    return await get_track(key, track_id, fmt)


async def get_track(key: str, track_id: str, fmt: str) -> Response:
    track_fmt: TrackFormat = TrackFormat[fmt]
    track: Optional[LogTrack] = controller.get_track(key, track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"{key} {track_id} not found")

    track_str = track.get_track_fmt_string(track_fmt)
    return Response(content=track_str, media_type=track_fmt.content_type())
