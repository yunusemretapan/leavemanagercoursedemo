from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    # Every test gets its own fresh SQLite file (docs/testing.md, Resource hygiene 5).
    return Settings(db_path=tmp_path / "test.db")


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    # Always `with`: without it the lifespan (migrations) does not run (Known traps).
    with TestClient(create_app(settings)) as test_client:
        yield test_client
