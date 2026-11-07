import logging
import sqlite3
import threading
import time
from datetime import timedelta

import pytest

import app.business.auth as auth_module
from app.business import passwords
from app.business.auth import AuthService
from app.business.login_throttle import ACCOUNT_LIMIT, IP_LIMIT, LoginThrottle
from app.data.database import Database
from app.models.errors import InvalidCredentials, TooManyAttempts
from tests.conftest import FAST_SCRYPT, FakeClock

USER = "ali.demir"
IP = "10.0.0.1"


@pytest.fixture
def throttle(seeded_db: Database, clock: FakeClock) -> LoginThrottle:
    return LoginThrottle(seeded_db, clock)


def _fail(throttle: LoginThrottle, username: str = USER, ip: str = IP) -> None:
    throttle.failed(throttle.reserve(username, ip))


def _rows(db: Database, sql: str) -> list[tuple[object, ...]]:
    conn = sqlite3.connect(db.path)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def test_fifth_failure_locks_even_correct_password_without_verifying(
    throttle: LoginThrottle,
) -> None:
    for _ in range(ACCOUNT_LIMIT):
        _fail(throttle)
    # The next attempt is refused before any password could be checked (reserve raises).
    with pytest.raises(TooManyAttempts) as caught:
        throttle.reserve(USER, "10.0.0.2")
    assert caught.value.code == "TOO_MANY_ATTEMPTS"
    assert caught.value.retry_after == 15 * 60


def test_four_failures_then_success(throttle: LoginThrottle) -> None:
    for _ in range(ACCOUNT_LIMIT - 1):
        _fail(throttle)
    throttle.succeeded(throttle.reserve(USER, IP))  # admitted: not locked


def test_success_resets_user_counter(throttle: LoginThrottle) -> None:
    for _ in range(ACCOUNT_LIMIT - 1):
        _fail(throttle)
    throttle.succeeded(throttle.reserve(USER, IP))
    for _ in range(ACCOUNT_LIMIT - 1):
        _fail(throttle)
    throttle.succeeded(throttle.reserve(USER, IP))  # still admitted


def test_failures_older_than_window_do_not_count(throttle: LoginThrottle, clock: FakeClock) -> None:
    for _ in range(ACCOUNT_LIMIT - 1):
        _fail(throttle)
    clock.advance(timedelta(minutes=15, seconds=1))
    _fail(throttle)  # only one failure inside the window now
    throttle.succeeded(throttle.reserve(USER, IP))


def test_lock_lifts_after_15_minutes_and_is_not_extended(
    throttle: LoginThrottle, clock: FakeClock
) -> None:
    for _ in range(ACCOUNT_LIMIT):
        _fail(throttle)
    clock.advance(timedelta(minutes=10))
    with pytest.raises(TooManyAttempts) as caught:
        throttle.reserve(USER, IP)  # an attempt during the lock: not counted, no extension
    assert caught.value.retry_after == 5 * 60
    clock.advance(timedelta(minutes=5))
    throttle.succeeded(throttle.reserve(USER, IP))  # exactly 15 min after the 5th failure


def test_unknown_username_locks_identically(throttle: LoginThrottle) -> None:
    for _ in range(ACCOUNT_LIMIT):
        _fail(throttle, username="kimse.yok")
    with pytest.raises(TooManyAttempts) as caught:
        throttle.reserve("kimse.yok", IP)
    assert caught.value.retry_after == 15 * 60


def test_ip_limit_after_20_failures_any_username(throttle: LoginThrottle) -> None:
    for i in range(IP_LIMIT):
        _fail(throttle, username=f"user{i}")  # never 5 for one username
    with pytest.raises(TooManyAttempts):
        throttle.reserve("zeynep.sahin", IP)
    throttle.succeeded(throttle.reserve("zeynep.sahin", "10.0.0.9"))  # other address unaffected


def test_success_does_not_reset_ip_counter(throttle: LoginThrottle) -> None:
    for i in range(IP_LIMIT - 1):
        _fail(throttle, username=f"user{i}")
    throttle.succeeded(throttle.reserve("zeynep.sahin", IP))
    _fail(throttle, username="user99")  # the 20th failure
    with pytest.raises(TooManyAttempts):
        throttle.reserve("zeynep.sahin", IP)


def test_retry_after_is_max_of_limits_rounded_up(throttle: LoginThrottle, clock: FakeClock) -> None:
    for i in range(IP_LIMIT - ACCOUNT_LIMIT):
        _fail(throttle, username=f"user{i}")
        clock.advance(timedelta(seconds=10))
    clock.advance(timedelta(seconds=0.5))
    for _ in range(ACCOUNT_LIMIT):
        _fail(throttle)  # 20 address failures; the account locks at this moment
    # IP window frees when the oldest failure (at t=0) leaves: 15 min - 150.5 s from now.
    # The account lock ends 15 min from now: the larger wait wins.
    with pytest.raises(TooManyAttempts) as caught:
        throttle.reserve(USER, IP)
    assert caught.value.retry_after == 15 * 60
    with pytest.raises(TooManyAttempts) as ip_only:
        throttle.reserve("zeynep.sahin", IP)
    assert ip_only.value.retry_after == 900 - 150  # 749.5 s rounded up


def test_old_records_are_purged_on_attempt(
    throttle: LoginThrottle, clock: FakeClock, seeded_db: Database
) -> None:
    for _ in range(ACCOUNT_LIMIT):
        _fail(throttle)
    clock.advance(timedelta(minutes=16))
    throttle.succeeded(throttle.reserve("zeynep.sahin", "10.0.0.9"))
    assert _rows(seeded_db, "SELECT COUNT(*) FROM login_failures") == [(0,)]
    assert _rows(seeded_db, "SELECT COUNT(*) FROM account_locks") == [(0,)]


def test_lock_logs_one_warning_without_password(
    throttle: LoginThrottle, clock: FakeClock, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="app.auth"):
        for _ in range(ACCOUNT_LIMIT):
            _fail(throttle)
    records = [r for r in caplog.records if r.name == "app.auth"]
    assert len(records) == 1
    line = records[0].getMessage()
    assert line == f"account locked username={USER} ip={IP} at=2026-11-09T09:00:00.000000Z"


def test_lock_log_line_escapes_control_characters(
    throttle: LoginThrottle, caplog: pytest.LogCaptureFixture
) -> None:
    forged = "x\naccount locked username=zeynep.sahin ip=1.2.3.4 at=2026-11-09T09:00:00.000000Z"
    with caplog.at_level(logging.WARNING, logger="app.auth"):
        for _ in range(ACCOUNT_LIMIT):
            _fail(throttle, username=forged, ip="10.0.0.1\r\n")
    records = [r for r in caplog.records if r.name == "app.auth"]
    assert len(records) == 1
    line = records[0].getMessage()
    assert "\n" not in line
    assert "\r" not in line
    assert line == (
        "account locked username=x\\x0aaccount\\x20locked\\x20username=zeynep.sahin"
        "\\x20ip=1.2.3.4\\x20at=2026-11-09T09:00:00.000000Z ip=10.0.0.1\\x0d\\x0a"
        " at=2026-11-09T09:00:00.000000Z"
    )


def test_concurrent_wrong_attempts_verify_at_most_five(throttle: LoginThrottle) -> None:
    admitted: list[int] = []
    refused: list[int] = []
    barrier = threading.Barrier(10)

    def attempt(i: int) -> None:
        barrier.wait()
        try:
            throttle.reserve(USER, f"10.0.1.{i}")
            admitted.append(i)  # only admitted attempts would reach password verification
        except TooManyAttempts:
            refused.append(i)

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert len(admitted) == ACCOUNT_LIMIT
    assert len(refused) == 10 - ACCOUNT_LIMIT


def test_concurrent_wrong_logins_verify_password_at_most_five(
    seeded_db: Database,
    clock: FakeClock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # End to end through AuthService: a slowed verification keeps every admitted attempt in
    # flight, so only the reserve transaction can stop the other five (review F-2).
    verified: list[int] = []
    real_verify = passwords.verify_password

    def slow_verify(password: str, stored: str) -> bool:
        verified.append(1)
        time.sleep(0.2)
        return real_verify(password, stored)

    monkeypatch.setattr(auth_module, "verify_password", slow_verify)
    auth = AuthService(seeded_db, clock, FAST_SCRYPT)
    outcomes: list[str] = []
    barrier = threading.Barrier(10)

    def attempt(i: int) -> None:
        barrier.wait()
        try:
            auth.login(USER, "yanlis parola denemesi", client_ip=f"10.0.1.{i}")
            outcomes.append("logged in")
        except InvalidCredentials:
            outcomes.append("invalid")
        except TooManyAttempts:
            outcomes.append("refused")
        except Exception as exc:  # any other error must fail the test, not hide in a thread
            outcomes.append(f"error: {exc!r}")

    with caplog.at_level(logging.WARNING, logger="app.auth"):
        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
    assert sorted(outcomes) == ["invalid"] * ACCOUNT_LIMIT + ["refused"] * (10 - ACCOUNT_LIMIT)
    assert len(verified) == ACCOUNT_LIMIT
    locks = [r for r in caplog.records if r.name == "app.auth"]
    assert len(locks) == 1
