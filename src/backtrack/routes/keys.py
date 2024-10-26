from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from backtrack.controllers import controller

keys_router: APIRouter = APIRouter()


@keys_router.get("/{key}/profile/{name}", response_class=PlainTextResponse)
def profile(key: str, name: str):
    return controller.make_profile(key, name)
