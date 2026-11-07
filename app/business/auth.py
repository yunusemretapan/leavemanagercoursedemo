"""Login, server-side sessions and logout (spec 0002 R-5…R-9; ADR 0001)."""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import timedelta

from app.business.passwords import PRODUCTION_SCRYPT, ScryptParams, dummy_hash, verify_password
from app.data.database import Database
from app.data.sessions import SessionRepository
from app.data.users import UserRepository
from app.models.clock import Clock
from app.models.errors import InvalidCredentials, SessionExpired, Unauthenticated
from app.models.user import User

IDLE_TIMEOUT = timedelta(minutes=30)
ABSOLUTE_TIMEOUT = timedelta(hours=8)
TOKEN_BYTES = 32


def token_digest(token: str) -> str:
    """Only this digest is stored; the browser token itself never reaches the database."""
    return hashlib.sha256(token.encode("ascii", errors="replace")).hexdigest()


def normalize_username(username: str) -> str:
    return username.strip().lower()


@dataclass(frozen=True)
class LoginResult:
    user: User
    token: str


class AuthService:
    def __init__(
        self, db: Database, clock: Clock, params: ScryptParams = PRODUCTION_SCRYPT
    ) -> None:
        self._db = db
        self._clock = clock
        # Unknown usernames are verified against this, so they cost as much as a wrong password.
        self._dummy_hash = dummy_hash(params)

    def login(self, username: str, password: str, previous_token: str | None = None) -> LoginResult:
        with self._db.connect() as conn:
            found = UserRepository(conn).get_with_hash(normalize_username(username))
        # Verify outside the connection: scrypt is deliberately slow.
        password_ok = verify_password(password, found[1] if found else self._dummy_hash)
        if found is None or not password_ok:
            raise InvalidCredentials()
        user = found[0]
        now = self._clock.now()
        token = secrets.token_urlsafe(TOKEN_BYTES)
        with self._db.connect() as conn:
            sessions = SessionRepository(conn)
            if previous_token:
                sessions.delete(token_digest(previous_token))
            sessions.delete_expired(now - IDLE_TIMEOUT, now - ABSOLUTE_TIMEOUT)
            sessions.create(token_digest(token), user.id, now)
        return LoginResult(user=user, token=token)

    def authenticate(self, token: str | None) -> User:
        """The session's user; Unauthenticated or SessionExpired otherwise."""
        if not token:
            raise Unauthenticated()
        digest = token_digest(token)
        now = self._clock.now()
        expired = False
        user: User | None = None
        with self._db.connect() as conn:
            sessions = SessionRepository(conn)
            record = sessions.get(digest)
            if record is None:
                raise Unauthenticated()
            idle = now - record.last_seen_at
            age = now - record.created_at
            if idle > IDLE_TIMEOUT or age > ABSOLUTE_TIMEOUT:
                sessions.delete(digest)
                expired = True  # raised after the block so the delete is committed
            else:
                sessions.touch(digest, now)
                user = UserRepository(conn).get_by_id(record.user_id)
        if expired:
            raise SessionExpired()
        if user is None:
            raise Unauthenticated()
        return user

    def logout(self, token: str | None) -> None:
        """Idempotent: no session, nothing to do."""
        if not token:
            return
        with self._db.connect() as conn:
            SessionRepository(conn).delete(token_digest(token))
