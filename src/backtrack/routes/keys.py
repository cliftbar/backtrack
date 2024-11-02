from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from backtrack.controllers import controller

keys_router: APIRouter = APIRouter()


@keys_router.get("/profile/{key}", response_class=PlainTextResponse)
async def profile(key: str, track_id: str):
    return controller.make_profile(key, track_id)

@keys_router.get("/next-sqid")
async def get_sqid():
    new_id: str = await controller.get_next_squid()
    return {"key": new_id}
