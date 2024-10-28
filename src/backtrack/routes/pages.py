from datetime import datetime, timezone
from typing import Optional

from fastapi import Request, APIRouter
from fastapi.responses import PlainTextResponse, HTMLResponse
from starlette.templating import Jinja2Templates

from backtrack.config import app_conf
from backtrack.controllers import controller
from backtrack.storage.models import LogTrack

pages_router: APIRouter = APIRouter()
templates = Jinja2Templates(directory=app_conf.general.template_dir)


@pages_router.get('/robots.txt', response_class=PlainTextResponse)
def robots():
    data = """User-agent: *\nDisallow: /"""
    return data


@pages_router.get("/", response_class=HTMLResponse)
async def home_page(request: Request, key: Optional[str] = None):
    new_key: str = key if key is not None else await controller.get_next_squid()
    return templates.TemplateResponse(
        request=request, name="html/home.jinja", context={"user_default": new_key,
                                                          "track_default": f"track_{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}"}
    )


@pages_router.get("/map.html", response_class=HTMLResponse)
async def map_page(request: Request, key: Optional[str] = None):
    tracks: list[LogTrack] = await controller.get_tracks(key)
    return templates.TemplateResponse(request=request, name="html/map.jinja", context={"tracks": tracks, "key": key, "hostname": app_conf.general.hostname})
