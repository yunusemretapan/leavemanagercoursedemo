import sqlite3
from datetime import timedelta

import pytest

from app.business.auth import AuthService, token_digest
from app.data.database import Database
from app.models.errors import InvalidCredentials, SessionExpired, Unauthenticated
from app.models.user import Role
from tests.conftest import FAST_SCRYPT, TEST_DEMO_PASSWORD, FakeClock


@pytest.fixture
def auth(seeded_db: Database, clock: FakeClock) -> AuthService:
    return AuthService(seeded_db, clock, FAST_SCRYPT)


def _session_count(db: Database) -> int:
    conn = sqlite3.connect(db.path)
    try:
        return int(conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0])
    finally:
        conn.close()


def test_login_trims_and_ignores_username_case(auth: AuthService) -> None:
    result = auth.login("  Ali.Demir ", TEST_DEMO_PASSWORD)
    assert result.user.username == "ali.demir"
    assert result.user.role is Role.EMPLOYEE
    assert auth.authenticate(result.token) == result.user


def test_wrong_password_and_unknown_user_raise_the_same_error(auth: AuthService) -> None:
    with pytest.raises(InvalidCredentials):
        auth.login("ali.demir", TEST_DEMO_PASSWORD + "x")
    with pytest.raises(InvalidCredentials):
        auth.login("nobody.here", TEST_DEMO_PASSWORD)


def test_session_survives_activity_until_absolute_limit(
    auth: AuthService, clock: FakeClock
) -> None:
    token = auth.login("ali.demir", TEST_DEMO_PASSWORD).token
    # 29-minute steps for 8 hours: never idle too long, still under the absolute limit.
    for _ in range(16):
        clock.advance(timedelta(minutes=29))
        auth.authenticate(token)
    clock.advance(timedelta(minutes=16))  # 8 h exactly since login
    assert auth.authenticate(token).username == "ali.demir"


def test_idle_timeout_expires_and_deletes_session(
    auth: AuthService, clock: FakeClock, seeded_db: Database
) -> None:
    token = auth.login("ali.demir", TEST_DEMO_PASSWORD).token
    clock.advance(timedelta(minutes=30))
    auth.authenticate(token)  # exactly 30 min idle is still valid
    clock.advance(timedelta(minutes=30, seconds=1))
    with pytest.raises(SessionExpired):
        auth.authenticate(token)
    assert _session_count(seeded_db) == 0
    with pytest.raises(Unauthenticated):  # deleted: now simply unknown
        auth.authenticate(token)


def test_absolute_timeout_expires_despite_activity(auth: AuthService, clock: FakeClock) -> None:
    token = auth.login("ali.demir", TEST_DEMO_PASSWORD).token
    for _ in range(16):
        clock.advance(timedelta(minutes=29))
        auth.authenticate(token)
    clock.advance(timedelta(minutes=17))  # 8 h 1 min since login, last request 17 min ago
    with pytest.raises(SessionExpired):
        auth.authenticate(token)


def test_logout_invalidates_only_this_session(auth: AuthService) -> None:
    first = auth.login("ali.demir", TEST_DEMO_PASSWORD).token
    other_device = auth.login("ali.demir", TEST_DEMO_PASSWORD).token
    auth.logout(first)
    with pytest.raises(Unauthenticated):
        auth.authenticate(first)
    assert auth.authenticate(other_device).username == "ali.demir"
    auth.logout(first)  # idempotent
    auth.logout(None)


def test_relogin_issues_new_token_and_drops_old(auth: AuthService) -> None:
    old = auth.login("ali.demir", TEST_DEMO_PASSWORD).token
    new = auth.login("ali.demir", TEST_DEMO_PASSWORD, previous_token=old).token
    assert new != old
    with pytest.raises(Unauthenticated):
        auth.authenticate(old)
    assert auth.authenticate(new).username == "ali.demir"


def test_login_purges_expired_sessions(
    auth: AuthService, clock: FakeClock, seeded_db: Database
) -> None:
    auth.login("zeynep.sahin", TEST_DEMO_PASSWORD)
    clock.advance(timedelta(hours=9))
    auth.login("ali.demir", TEST_DEMO_PASSWORD)
    assert _session_count(seeded_db) == 1


def test_only_token_digest_is_stored(auth: AuthService, seeded_db: Database) -> None:
    token = auth.login("ali.demir", TEST_DEMO_PASSWORD).token
    conn = sqlite3.connect(seeded_db.path)
    try:
        stored = [row[0] for row in conn.execute("SELECT token_hash FROM sessions")]
    finally:
        conn.close()
    assert stored == [token_digest(token)]
    assert token not in stored


def test_missing_or_unknown_token_is_unauthenticated(auth: AuthService) -> None:
    for token in (None, "", "not-a-real-token"):
        with pytest.raises(Unauthenticated):
            auth.authenticate(token)
