import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.data.migrations import MIGRATIONS_DIR
from app.main import create_app

pytestmark = pytest.mark.integration

ALL_VERSIONS = sorted(p.stem for p in MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql"))


def _start_and_stop(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/health").status_code == 200


def _query(db_path: Path, sql: str) -> list[tuple[str, ...]]:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def test_first_start_applies_all_migrations(settings: Settings) -> None:
    assert not settings.db_path.exists()

    _start_and_stop(settings)

    assert settings.db_path.exists()
    assert ALL_VERSIONS  # at least one migration exists
    applied = [r[0] for r in _query(settings.db_path, "SELECT version FROM schema_migrations")]
    assert sorted(applied) == ALL_VERSIONS
    tables = {r[0] for r in _query(settings.db_path, "SELECT name FROM sqlite_master")}
    assert "app_meta" in tables


def test_second_start_reapplies_nothing_and_keeps_data(settings: Settings) -> None:
    _start_and_stop(settings)
    conn = sqlite3.connect(settings.db_path)
    with conn:
        conn.execute("INSERT INTO app_meta (key, value) VALUES ('marker', 'kept')")
    conn.close()

    # Re-running 0001 would fail (CREATE TABLE without IF NOT EXISTS) and abort startup.
    _start_and_stop(settings)

    applied = [r[0] for r in _query(settings.db_path, "SELECT version FROM schema_migrations")]
    assert sorted(applied) == ALL_VERSIONS
    rows = _query(settings.db_path, "SELECT value FROM app_meta WHERE key = 'marker'")
    assert rows == [("kept",)]
