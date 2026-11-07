"""FastAPI dependencies: hand the composition root's objects to the routers."""

from typing import Annotated, cast

from fastapi import Depends, Request

from app.business.auth import AuthService
from app.business.health import Pingable
from app.models.user import User

SESSION_COOKIE = "lm_session"


def get_database(request: Request) -> Pingable:
    return cast(Pingable, request.app.state.database)


def get_auth(request: Request) -> AuthService:
    return cast(AuthService, request.app.state.auth)


def current_user(request: Request, auth: Annotated[AuthService, Depends(get_auth)]) -> User:
    """The signed-in user; Unauthenticated / SessionExpired become 401 (app/api/errors.py)."""
    return auth.authenticate(request.cookies.get(SESSION_COOKIE))
