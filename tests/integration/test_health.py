from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.data.database import Database

pytestmark = pytest.mark.integration


def test_health_ok_when_database_reachable(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_503_when_database_unreachable(client: TestClient, tmp_path: Path) -> None:
    # A directory is not an openable SQLite file: the data store is unreachable.
    unreachable = tmp_path / "not-a-database"
    unreachable.mkdir()
    client.app.state.database = Database(unreachable)  # type: ignore[attr-defined]

    response = client.get("/api/health")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert body["error"]["message"]
    assert str(tmp_path) not in response.text
    assert "sqlite" not in response.text.lower()
