"""SQLite access: the only place that opens connections (docs/architecture.md)."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.models.errors import ServiceUnavailable


def _is_contention(exc: BaseException) -> bool:
    if not isinstance(exc, sqlite3.OperationalError):
        return False
    message = str(exc).lower()
    return "locked" in message or "busy" in message


class Database:
    """One SQLite file. Every caller gets its own short-lived connection (Known traps)."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connect(self, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        """Open a connection with foreign keys on; commit on success, roll back on error.

        immediate=True takes SQLite's write lock before the first read (BEGIN IMMEDIATE), so a
        check-then-insert cannot race another connection (spec 0003 R-1a). Concurrent writers
        wait up to the connect timeout (5 s) instead of failing. The guarantee comes from this
        flag, not from statement order: a default (deferred) transaction only serialises if its
        first statement happens to be a write, and a deferred read-then-write fails with
        "database is locked" under contention (test_immediate_connection_holds_write_lock...).
        """
        try:
            conn = sqlite3.connect(self.path, autocommit=True)
        except sqlite3.Error as exc:
            raise ServiceUnavailable() from exc
        try:
            # PRAGMA foreign_keys is a no-op inside a transaction: set it before one opens.
            conn.execute("PRAGMA foreign_keys=ON")
            if immediate:
                conn.execute("BEGIN IMMEDIATE")
            else:
                conn.autocommit = False
        except sqlite3.Error as exc:
            conn.close()  # e.g. BEGIN IMMEDIATE timed out: do not leak the connection
            raise ServiceUnavailable() from exc
        try:
            yield conn
            if immediate:
                conn.execute("COMMIT")
            else:
                conn.commit()
        except BaseException as exc:
            if immediate:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
            else:
                conn.rollback()
            if _is_contention(exc):
                # Safety net: lock contention is a temporary outage (503), not a bug (500).
                raise ServiceUnavailable() from exc
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
