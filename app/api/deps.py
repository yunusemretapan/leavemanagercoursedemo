"""FastAPI dependencies: hand the composition root's objects to the routers."""

from typing import cast

from fastapi import Request

from app.business.health import Pingable


def get_database(request: Request) -> Pingable:
    return cast(Pingable, request.app.state.database)
