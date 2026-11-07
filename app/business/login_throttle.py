"""Brute force protection: account lock and client-address limit (spec 0003; ADR 0002).

An attempt is counted as a failure *before* the password is verified ("reserve"), inside one
BEGIN IMMEDIATE transaction with the limit check, so concurrent attempts cannot slip past the
limit (R-1a). The outcome then confirms it ("failed") or takes it back ("succeeded").
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.data.database import Database
from app.data.login_attempts import AttemptKind, LoginAttemptRepository
from app.data.sessions import to_iso
from app.models.clock import Clock
from app.models.errors import TooManyAttempts

ACCOUNT_LIMIT = 5
IP_LIMIT = 20
WINDOW = timedelta(minutes=15)
LOCK_DURATION = timedelta(minutes=15)

logger = logging.getLogger("app.auth")


@dataclass(frozen=True)
class Reservation:
    username: str
    ip: str
    at: datetime
    ip_failure_id: int


def _seconds(wait: timedelta) -> int:
    return max(1, math.ceil(wait.total_seconds()))


def _log_safe(value: str) -> str:
    """Escape control and whitespace characters so a username cannot forge log lines (CWE-117)."""
    return "".join(f"\\x{ord(c):02x}" if c.isspace() or not c.isprintable() else c for c in value)


class LoginThrottle:
    def __init__(self, db: Database, clock: Clock) -> None:
        self._db = db
        self._clock = clock

    def reserve(self, username: str, ip: str) -> Reservation:
        """Count this attempt as a failure up front, or raise TooManyAttempts (nothing counted)."""
        now = self._clock.now()
        since = now - WINDOW
        waits: list[timedelta] = []
        ip_failure_id = 0
        with self._db.connect(immediate=True) as conn:
            attempts = LoginAttemptRepository(conn)
            attempts.purge(failures_before=since, locks_ended_by=now)
            locked_until = attempts.locked_until(username)
            if locked_until is not None and locked_until > now:
                waits.append(locked_until - now)
            ip_times = attempts.failure_times(AttemptKind.IP, ip, since)
            if len(ip_times) >= IP_LIMIT:
                # The window drops below the limit when this failure leaves it.
                waits.append(ip_times[len(ip_times) - IP_LIMIT] + WINDOW - now)
            if not waits and len(attempts.failure_times(AttemptKind.USER, username, since)) >= (
                ACCOUNT_LIMIT
            ):
                # Only in-flight attempts can fill the account counter (a 5th confirmed failure
                # turns into a lock): they will most likely end in a lock.
                waits.append(LOCK_DURATION)
            if not waits:
                attempts.add_failure(AttemptKind.USER, username, now)
                ip_failure_id = attempts.add_failure(AttemptKind.IP, ip, now)
        if waits:
            raise TooManyAttempts(retry_after=_seconds(max(waits)))
        return Reservation(username=username, ip=ip, at=now, ip_failure_id=ip_failure_id)

    def succeeded(self, reservation: Reservation) -> None:
        """A correct password: reset the account counter; the address counter is not reset."""
        with self._db.connect(immediate=True) as conn:
            attempts = LoginAttemptRepository(conn)
            attempts.delete_failures(AttemptKind.USER, reservation.username)
            # A lock created by a concurrent failure after this attempt was admitted is moot:
            # the password was right.
            attempts.unlock(reservation.username)
            attempts.delete_failure(reservation.ip_failure_id)

    def failed(self, reservation: Reservation) -> None:
        """A wrong password: the reserved failure stays; the 5th in the window starts a lock."""
        locked = False
        with self._db.connect(immediate=True) as conn:
            attempts = LoginAttemptRepository(conn)
            since = reservation.at - WINDOW
            failures = attempts.failure_times(AttemptKind.USER, reservation.username, since)
            current_lock = attempts.locked_until(reservation.username)
            already_locked = current_lock is not None and current_lock > reservation.at
            if len(failures) >= ACCOUNT_LIMIT and not already_locked:
                attempts.lock(reservation.username, reservation.at + LOCK_DURATION)
                # The lock consumes the counter: after it ends the user has 5 fresh attempts.
                attempts.delete_failures(AttemptKind.USER, reservation.username)
                locked = True
        if locked:
            logger.warning(
                "account locked username=%s ip=%s at=%s",
                _log_safe(reservation.username),
                _log_safe(reservation.ip),
                to_iso(reservation.at),
            )
