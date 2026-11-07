"""Server-side sessions: only token digests are stored (ADR 0001)."""

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class SessionRecord:
    token_hash: str
    user_id: int
    created_at: datetime
    last_seen_at: datetime


def to_iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def from_iso(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)


class SessionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create(self, token_hash: str, user_id: int, now: datetime) -> None:
        self._conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, last_seen_at)"
            " VALUES (?, ?, ?, ?)",
            (token_hash, user_id, to_iso(now), to_iso(now)),
        )

    def get(self, token_hash: str) -> SessionRecord | None:
        row = self._conn.execute(
            "SELECT token_hash, user_id, created_at, last_seen_at FROM sessions"
            " WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
        if row is None:
            return None
        return SessionRecord(str(row[0]), int(row[1]), from_iso(row[2]), from_iso(row[3]))

    def touch(self, token_hash: str, now: datetime) -> None:
        self._conn.execute(
            "UPDATE sessions SET last_seen_at = ? WHERE token_hash = ?",
            (to_iso(now), token_hash),
        )

    def delete(self, token_hash: str) -> None:
        self._conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))

    def delete_expired(self, idle_cutoff: datetime, absolute_cutoff: datetime) -> None:
        """Delete sessions idle since before idle_cutoff or created before absolute_cutoff."""
        self._conn.execute(
            "DELETE FROM sessions WHERE last_seen_at < ? OR created_at < ?",
            (to_iso(idle_cutoff), to_iso(absolute_cutoff)),
        )
