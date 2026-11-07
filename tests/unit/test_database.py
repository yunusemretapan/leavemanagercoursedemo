import sqlite3
from typing import Any

import pytest

from app.data.database import Database
from app.models.errors import ServiceUnavailable


def _try_write_lock(db: Database) -> None:
    other = sqlite3.connect(db.path, timeout=0, autocommit=True)
    try:
        other.execute("BEGIN IMMEDIATE")
        other.execute("ROLLBACK")
    finally:
        other.close()


def test_immediate_connection_holds_write_lock_before_any_write(seeded_db: Database) -> None:
    # The reserve check reads before it writes; the lock must not depend on statement order
    # (spec 0003 R-1a; review F-2).
    with seeded_db.connect(immediate=True) as conn:
        conn.execute("SELECT COUNT(*) FROM login_failures").fetchone()
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            _try_write_lock(seeded_db)
    _try_write_lock(seeded_db)  # released on commit


def test_default_connection_does_not_lock_on_read(seeded_db: Database) -> None:
    with seeded_db.connect() as conn:
        conn.execute("SELECT COUNT(*) FROM login_failures").fetchone()
        _try_write_lock(seeded_db)


def test_lock_timeout_is_service_unavailable_and_closes_connection(
    seeded_db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[sqlite3.Connection] = []
    real_connect = sqlite3.connect

    def short_timeout(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        conn: sqlite3.Connection = real_connect(*args, **{**kwargs, "timeout": 0})
        opened.append(conn)
        return conn

    holder = real_connect(seeded_db.path, autocommit=True)
    try:
        holder.execute("BEGIN IMMEDIATE")
        monkeypatch.setattr(sqlite3, "connect", short_timeout)
        with pytest.raises(ServiceUnavailable), seeded_db.connect(immediate=True):
            pass
    finally:
        holder.close()
    assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        opened[0].execute("SELECT 1")
