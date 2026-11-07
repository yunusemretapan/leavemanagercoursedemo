"""Login, logout and the current user (spec 0002)."""

from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from app.api.deps import SESSION_COOKIE, current_user, get_auth
from app.business.auth import AuthService
from app.business.passwords import MAX_LENGTH
from app.models.user import ROLE_LABELS_TR, User

router = APIRouter(prefix="/api")


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=MAX_LENGTH)


class UserResponse(BaseModel):
    username: str
    full_name: str
    role: str
    role_label: str

    @classmethod
    def of(cls, user: User) -> "UserResponse":
        return cls(
            username=user.username,
            full_name=user.full_name,
            role=user.role.value,
            role_label=ROLE_LABELS_TR[user.role],
        )


def _cookie_secure(request: Request) -> bool:
    return cast(bool, request.app.state.settings.cookie_secure)


@router.post("/auth/login")
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    auth: Annotated[AuthService, Depends(get_auth)],
) -> UserResponse:
    # The body model accepts JSON only: a form-encoded post never reaches here (CSRF, R-11).
    result = auth.login(
        body.username, body.password, previous_token=request.cookies.get(SESSION_COOKIE)
    )
    response.set_cookie(
        SESSION_COOKIE,
        result.token,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(request),
        path="/",
    )
    return UserResponse.of(result.user)


@router.post("/auth/logout", status_code=204)
def logout(
    request: Request, response: Response, auth: Annotated[AuthService, Depends(get_auth)]
) -> None:
    auth.logout(request.cookies.get(SESSION_COOKIE))
    response.delete_cookie(
        SESSION_COOKIE, path="/", httponly=True, samesite="lax", secure=_cookie_secure(request)
    )


@router.get("/me")
def me(user: Annotated[User, Depends(current_user)]) -> UserResponse:
    return UserResponse.of(user)
