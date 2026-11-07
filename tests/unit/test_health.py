import pytest

from app.business.health import check_health
from app.models.errors import ServiceUnavailable
from app.models.health import HealthStatus


class ReachableDb:
    def ping(self) -> None:
        return None


class DownDb:
    def ping(self) -> None:
        raise ServiceUnavailable()


def test_check_health_reports_ok_when_database_answers() -> None:
    assert check_health(ReachableDb()) == HealthStatus(status="ok", database="ok")


def test_check_health_raises_when_database_down() -> None:
    with pytest.raises(ServiceUnavailable):
        check_health(DownDb())
