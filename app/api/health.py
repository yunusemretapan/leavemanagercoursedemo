from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_database
from app.business.health import Pingable, check_health

router = APIRouter(prefix="/api")


class HealthResponse(BaseModel):
    status: str
    database: str


@router.get("/health")
def health(db: Annotated[Pingable, Depends(get_database)]) -> HealthResponse:
    result = check_health(db)
    return HealthResponse(status=result.status, database=result.database)
