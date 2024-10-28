from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from backtrack.controllers import controller

keys_router: APIRouter = APIRouter()


@keys_router.get("/profile/{key}", response_class=PlainTextResponse)
def profile(key: str, track_id: str):
    return controller.make_profile(key, track_id)
