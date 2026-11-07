import sqlite3

import pytest

from app.data.database import Database


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
