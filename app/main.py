"""Composition root: wires the layers together (docs/architecture.md)."""

import mimetypes
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.errors import register_error_handlers
from app.api.health import router as health_router
from app.business.auth import AuthService
from app.business.seed import seed_demo_users, validate_demo_password
from app.config import REPO_ROOT, Settings
from app.data.database import Database
from app.data.migrations import apply_migrations
from app.models.clock import Clock, SystemClock

WEB_DIR = REPO_ROOT / "web"


def _serve_js_as_javascript() -> None:
    # Windows may register .js as text/plain (HKCR\.js) and mimetypes reads that; browsers then
    # refuse ES module scripts (Known traps). add_type initialises the database itself if needed
    # and overrides the OS mapping; an explicit init() afterwards would re-read it and undo this.
    mimetypes.add_type("text/javascript", ".js")


def create_app(settings: Settings | None = None, clock: Clock | None = None) -> FastAPI:
    """Raises ConfigurationError (before anything starts) when DEMO_PASSWORD is missing or weak."""
    _serve_js_as_javascript()
    settings = settings or Settings.from_env()
    demo_password = validate_demo_password(settings.demo_password)
    database = Database(settings.db_path)
    auth = AuthService(database, clock or SystemClock(), settings.scrypt)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        apply_migrations(database)
        seed_demo_users(database, demo_password, settings.scrypt)
        yield

    app = FastAPI(title="Leave Manager", lifespan=lifespan)
    app.state.settings = settings
    app.state.database = database
    app.state.auth = auth
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    # Mounted last: /api/* routes match first; everything else is the static start page.
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app
