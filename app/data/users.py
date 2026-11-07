"""Users table access: parameterised SQL only (docs/security.md)."""

import sqlite3

from app.models.user import Role, User


def _to_user(row: sqlite3.Row | tuple[object, ...]) -> User:
    user_id, username, full_name, role, manager_id = tuple(row)
    return User(
        id=int(str(user_id)),
        username=str(username),
        full_name=str(full_name),
        role=Role(str(role)),
        manager_id=None if manager_id is None else int(str(manager_id)),
    )


class UserRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return int(row[0])

    def get_by_id(self, user_id: int) -> User | None:
        row = self._conn.execute(
            "SELECT id, username, full_name, role, manager_id FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return None if row is None else _to_user(row)

    def get_with_hash(self, username: str) -> tuple[User, str] | None:
        """The user and the stored password hash; username matches case-insensitively."""
        row = self._conn.execute(
            "SELECT id, username, full_name, role, manager_id, password_hash FROM users"
            " WHERE username = ?",
            (username,),
        ).fetchone()
        if row is None:
            return None
        return _to_user(row[:5]), str(row[5])

    def insert(
        self,
        username: str,
        full_name: str,
        role: Role,
        manager_id: int | None,
        password_hash: str,
    ) -> int:
        cursor = self._conn.execute(
            "INSERT INTO users (username, full_name, role, manager_id, password_hash)"
            " VALUES (?, ?, ?, ?, ?)",
            (username, full_name, role.value, manager_id, password_hash),
        )
        return int(cursor.lastrowid or 0)
