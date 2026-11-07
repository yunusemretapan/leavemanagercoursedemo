"""Composition root: wires the layers together (docs/architecture.md)."""

import mimetypes
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.errors import register_error_handlers
from app.api.health import router as health_router
from app.config import REPO_ROOT, Settings
from app.data.database import Database
from app.data.migrations import apply_migrations

WEB_DIR = REPO_ROOT / "web"


def _serve_js_as_javascript() -> None:
    # Windows may register .js as text/plain (HKCR\.js) and mimetypes reads that; browsers then
    # refuse ES module scripts (Known traps). init() first: a later init() would re-read the OS
    # mapping and undo add_type.
    mimetypes.init()
    mimetypes.add_type("text/javascript", ".js")


def create_app(settings: Settings | None = None) -> FastAPI:
    _serve_js_as_javascript()
    settings = settings or Settings.from_env()
    database = Database(settings.db_path)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        apply_migrations(database)
        yield

    app = FastAPI(title="Leave Manager", lifespan=lifespan)
    app.state.database = database
    register_error_handlers(app)
    app.include_router(health_router)
    # Mounted last: /api/* routes match first; everything else is the static start page.
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app
