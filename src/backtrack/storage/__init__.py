from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": True}
engine: Engine = create_engine(sqlite_url, echo=True, future=True, connect_args=connect_args)
async_sqlite_url = f"sqlite+aiosqlite:///{sqlite_file_name}"
async_engine: AsyncEngine = create_async_engine(async_sqlite_url, echo=True, future=True)
