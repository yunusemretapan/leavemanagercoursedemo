import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.conftest import TEST_DEMO_PASSWORD

pytestmark = pytest.mark.integration

EXPECTED = {
    ("ayse.yilmaz", "Ayşe Yılmaz", "MANAGER", None),
    ("mehmet.kaya", "Mehmet Kaya", "MANAGER", "ayse.yilmaz"),
    ("ali.demir", "Ali Demir", "EMPLOYEE", "ayse.yilmaz"),
    ("zeynep.sahin", "Zeynep Şahin", "EMPLOYEE", "ayse.yilmaz"),
    ("can.ozturk", "Can Öztürk", "EMPLOYEE", "mehmet.kaya"),
    ("elif.arslan", "Elif Arslan", "EMPLOYEE", "mehmet.kaya"),
}


def _start_and_stop(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/health").status_code == 200


def _rows(db_path: Path, sql: str) -> list[tuple[object, ...]]:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def _users(db_path: Path) -> set[tuple[object, ...]]:
    return set(
        _rows(
            db_path,
            "SELECT u.username, u.full_name, u.role, m.username"
            " FROM users u LEFT JOIN users m ON m.id = u.manager_id",
        )
    )


def test_first_start_seeds_six_demo_users_with_managers(settings: Settings) -> None:
    _start_and_stop(settings)
    assert _users(settings.db_path) == EXPECTED


def test_second_start_keeps_six_users(settings: Settings) -> None:
    _start_and_stop(settings)
    hashes_before = _rows(settings.db_path, "SELECT password_hash FROM users ORDER BY id")
    _start_and_stop(settings)
    assert _users(settings.db_path) == EXPECTED
    assert _rows(settings.db_path, "SELECT password_hash FROM users ORDER BY id") == hashes_before


def test_no_plaintext_password_in_database(settings: Settings) -> None:
    _start_and_stop(settings)
    hashes = [str(r[0]) for r in _rows(settings.db_path, "SELECT password_hash FROM users")]
    assert len(set(hashes)) == 6  # same password, six different stored values
    assert all(h.startswith("scrypt$") for h in hashes)
    raw = settings.db_path.read_bytes()
    assert TEST_DEMO_PASSWORD.encode("utf-8") not in raw
