from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.business.passwords import ScryptParams
from app.business.seed import seed_demo_users
from app.config import Settings
from app.data.database import Database
from app.data.migrations import apply_migrations
from app.main import create_app

# Cheap scrypt for tests; production parameters are proven separately (spec 0002 Constraints).
FAST_SCRYPT = ScryptParams(n=2**10, r=8, p=1)
TEST_DEMO_PASSWORD = "kurs demosu icin test parolasi"  # noqa: S105 — fictional test value


class FakeClock:
    """Deterministic UTC clock (docs/testing.md, Determinism)."""

    def __init__(self, start: datetime | None = None) -> None:
        self.current = start or datetime(2026, 11, 9, 9, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def seeded_db(tmp_path: Path) -> Database:
    db = Database(tmp_path / "unit.db")
    apply_migrations(db)
    seed_demo_users(db, TEST_DEMO_PASSWORD, FAST_SCRYPT)
    return db


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    # Every test gets its own fresh SQLite file (docs/testing.md, Resource hygiene 5).
    return Settings(db_path=tmp_path / "test.db")


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    # Always `with`: without it the lifespan (migrations) does not run (Known traps).
    with TestClient(create_app(settings)) as test_client:
        yield test_client
