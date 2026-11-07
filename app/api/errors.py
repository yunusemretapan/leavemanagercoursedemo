"""The one error-handling pattern (docs/conventions.md, Error handling).

Every error leaves as ``{"error": {"code": ..., "message": ...}}``; internals never leak.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models.errors import (
    DomainError,
    InvalidCredentials,
    ServiceUnavailable,
    SessionExpired,
    Unauthenticated,
)

DEFAULT_DOMAIN_STATUS = 409
STATUS_BY_ERROR: dict[type[DomainError], int] = {
    ServiceUnavailable: 503,
    Unauthenticated: 401,
    SessionExpired: 401,
    InvalidCredentials: 401,
}
HTTP_ERRORS: dict[int, tuple[str, str]] = {
    404: ("NOT_FOUND", "İstenen kaynak bulunamadı."),
    405: ("METHOD_NOT_ALLOWED", "Bu işlem bu adreste desteklenmiyor."),
}
VALIDATION_ERROR = ("VALIDATION_ERROR", "İstek geçersiz. Lütfen girdiğiniz bilgileri kontrol edin.")
INTERNAL_ERROR = (
    "INTERNAL_ERROR",
    "Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
)


def error_body(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}


def status_for(error: DomainError) -> int:
    for cls in type(error).__mro__:
        if cls in STATUS_BY_ERROR:
            return STATUS_BY_ERROR[cls]
    return DEFAULT_DOMAIN_STATUS


async def _domain_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)  # noqa: S101 — registered for DomainError only
    return JSONResponse(error_body(exc.code, exc.message), status_code=status_for(exc))


async def _http_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)  # noqa: S101 — registered for it only
    code, message = HTTP_ERRORS.get(exc.status_code, ("HTTP_ERROR", "İstek işlenemedi."))
    return JSONResponse(error_body(code, message), status_code=exc.status_code)


async def _validation_error(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(error_body(*VALIDATION_ERROR), status_code=422)


async def _unexpected_error(_: Request, __: Exception) -> JSONResponse:
    # Details go to the server log (uvicorn logs the exception); the client gets a generic body.
    return JSONResponse(error_body(*INTERNAL_ERROR), status_code=500)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _unexpected_error)
