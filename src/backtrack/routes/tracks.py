from typing import Sequence

from fastapi import HTTPException, APIRouter
from geojson import LineString, FeatureCollection, Feature
from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, Session

from backtrack.controllers import controller
from backtrack.storage import async_engine, engine
from backtrack.storage.models import LogTrack, LogItem, LogPoint

tracks_router: APIRouter = APIRouter()


@tracks_router.post("/log")
async def store_log(log_item: LogItem):
    # print(log_item)
    track: LogTrack = LogTrack.from_item(log_item)
    point: LogPoint = LogPoint.from_item(log_item)
    # print(track)
    # print(point)

    await controller.store_log(track, point)
    # print(f"point for {log_item.default_track_id()} saved")


@tracks_router.post("/track")
async def store_log(log_item: LogItem):
    track: LogTrack = LogTrack.from_item(log_item)
    point: LogPoint = LogPoint.from_item(log_item)
    print(track)
    print(point)


@tracks_router.get("/tracks")
async def get_log(key: str):
    tracks = controller.get_tracks(key)
    if not tracks:
        raise HTTPException(status_code=404, detail=f"{key} not found")


@tracks_router.get("/track")
async def get_log(key: str, track_id: str, format: str = "json"):
    collection = controller.get_json_track(key, track_id)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"{key} {track_id} not found")
    return collection


@tracks_router.get("/{key}/track/{track_id}/{file_fmt}")
async def get_log(key: str, track_id: str, file_fmt: str):
    collection = controller.get_json_track(key, track_id)
    if not collection:
        raise HTTPException(status_code=404, detail=f"{key} {track_id} not found")
    return collection
