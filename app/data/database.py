"""SQLite access: the only place that opens connections (docs/architecture.md)."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.models.errors import ServiceUnavailable


class Database:
    """One SQLite file. Every caller gets its own short-lived connection (Known traps)."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connect(self, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        """Open a connection with foreign keys on; commit on success, roll back on error.

        immediate=True takes SQLite's write lock before the first read (BEGIN IMMEDIATE), so a
        check-then-insert cannot race another connection (spec 0003 R-1a). Concurrent writers
        wait up to the connect timeout (5 s) instead of failing.
        """
        try:
            conn = sqlite3.connect(self.path, autocommit=True)
            # PRAGMA foreign_keys is a no-op inside a transaction: set it before one opens.
            conn.execute("PRAGMA foreign_keys=ON")
            if immediate:
                conn.execute("BEGIN IMMEDIATE")
            else:
                conn.autocommit = False
        except sqlite3.Error as exc:
            raise ServiceUnavailable() from exc
        try:
            yield conn
            if immediate:
                conn.execute("COMMIT")
            else:
                conn.commit()
        except BaseException:
            if immediate:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
            else:
                conn.rollback()
            raise
        finally:
            conn.close()

    def ping(self) -> None:
        """Raise ServiceUnavailable unless the database answers a trivial query."""
        try:
            with self.connect() as conn:
                conn.execute("SELECT 1").fetchone()
        except sqlite3.Error as exc:
            raise ServiceUnavailable() from exc
