"""Failed-login counters and account locks (spec 0003). Parameterised SQL only."""

import sqlite3
from datetime import datetime
from enum import StrEnum

from app.data.sessions import from_iso, to_iso


class AttemptKind(StrEnum):
    USER = "USER"
    IP = "IP"


class LoginAttemptRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def purge(self, failures_before: datetime, locks_ended_by: datetime) -> None:
        """Delete failures older than the window and locks that have ended (R-6)."""
        self._conn.execute(
            "DELETE FROM login_failures WHERE attempted_at < ?", (to_iso(failures_before),)
        )
        self._conn.execute(
            "DELETE FROM account_locks WHERE locked_until <= ?", (to_iso(locks_ended_by),)
        )

    def unlock(self, username: str) -> None:
        self._conn.execute("DELETE FROM account_locks WHERE username = ?", (username,))

    def add_failure(self, kind: AttemptKind, key: str, at: datetime) -> int:
        cursor = self._conn.execute(
            "INSERT INTO login_failures (kind, key, attempted_at) VALUES (?, ?, ?)",
            (kind.value, key, to_iso(at)),
        )
        return int(cursor.lastrowid or 0)

    def delete_failure(self, failure_id: int) -> None:
        self._conn.execute("DELETE FROM login_failures WHERE id = ?", (failure_id,))

    def delete_failures(self, kind: AttemptKind, key: str) -> None:
        self._conn.execute(
            "DELETE FROM login_failures WHERE kind = ? AND key = ?", (kind.value, key)
        )

    def failure_times(self, kind: AttemptKind, key: str, since: datetime) -> list[datetime]:
        """Failure timestamps at or after since, oldest first."""
        rows = self._conn.execute(
            "SELECT attempted_at FROM login_failures"
            " WHERE kind = ? AND key = ? AND attempted_at >= ? ORDER BY attempted_at",
            (kind.value, key, to_iso(since)),
        ).fetchall()
        return [from_iso(str(row[0])) for row in rows]

    def lock(self, username: str, until: datetime) -> None:
        self._conn.execute(
            "INSERT INTO account_locks (username, locked_until) VALUES (?, ?)"
            " ON CONFLICT (username) DO UPDATE SET locked_until = excluded.locked_until",
            (username, to_iso(until)),
        )

    def locked_until(self, username: str) -> datetime | None:
        row = self._conn.execute(
            "SELECT locked_until FROM account_locks WHERE username = ?", (username,)
        ).fetchone()
        return None if row is None else from_iso(str(row[0]))
