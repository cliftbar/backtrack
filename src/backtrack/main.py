from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backtrack.config import app_conf
from backtrack.routes.keys import keys_router
from backtrack.routes.pages import pages_router
from backtrack.routes.tracks import tracks_router
from backtrack.storage.db import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    create_db_and_tables()
    yield


backtrack_app = FastAPI(lifespan=lifespan)

backtrack_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

backtrack_app.mount("/static", StaticFiles(directory=app_conf.general.static_dir), name="static")

backtrack_app.include_router(tracks_router)
backtrack_app.include_router(pages_router)
backtrack_app.include_router(keys_router)