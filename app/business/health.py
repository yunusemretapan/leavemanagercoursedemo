"""Health use case: is the application and its data store reachable?"""

from typing import Protocol

from app.models.health import HealthStatus


class Pingable(Protocol):
    def ping(self) -> None:
        """Raise ServiceUnavailable when the data store cannot be reached."""


def check_health(db: Pingable) -> HealthStatus:
    """Return ok when the data store answers; ServiceUnavailable propagates otherwise."""
    db.ping()
    return HealthStatus(status="ok", database="ok")
