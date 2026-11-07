import logging
import sqlite3
from collections.abc import Iterator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from httpx import Response

import app.business.auth as auth_module
from app.business import passwords
from app.config import Settings
from app.main import create_app
from tests.conftest import TEST_DEMO_PASSWORD, FakeClock

pytestmark = pytest.mark.integration

TOO_MANY = {
    "error": {
        "code": "TOO_MANY_ATTEMPTS",
        "message": "Çok fazla başarısız giriş denemesi. Lütfen 15 dakika sonra tekrar deneyin.",
    }
}


def _client_at(settings: Settings, clock: FakeClock, host: str) -> TestClient:
    return TestClient(create_app(settings, clock), client=(host, 50000))


@pytest.fixture
def client_a(settings: Settings, clock: FakeClock) -> Iterator[TestClient]:
    with _client_at(settings, clock, "10.0.0.1") as client:
        yield client


def _login(client: TestClient, username: str, password: str, **headers: str) -> Response:
    response: Response = client.post(
        "/api/auth/login", json={"username": username, "password": password}, headers=headers
    )
    return response


def _wrong(client: TestClient, username: str = "ali.demir", times: int = 5) -> None:
    for _ in range(times):
        response = _login(client, username, "yanlis parola denemesi")
        assert response.status_code == 401


def test_locked_login_returns_429_even_with_correct_password(
    client_a: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _wrong(client_a)
    calls: list[str] = []
    real_verify = passwords.verify_password

    def spy(password: str, stored: str) -> bool:
        calls.append(stored)
        return real_verify(password, stored)

    monkeypatch.setattr(auth_module, "verify_password", spy)
    response = client_a.post(
        "/api/auth/login", json={"username": "ali.demir", "password": TEST_DEMO_PASSWORD}
    )
    assert response.status_code == 429
    assert response.json() == TOO_MANY
    assert response.headers["retry-after"] == str(15 * 60)
    assert "set-cookie" not in response.headers
    assert calls == []  # the password was never verified


def test_unknown_username_locks_identically(client_a: TestClient, clock: FakeClock) -> None:
    _wrong(client_a, "ali.demir")
    _wrong(client_a, "kimse.yok")
    clock.advance(timedelta(seconds=30))
    existing = client_a.post(
        "/api/auth/login", json={"username": "ali.demir", "password": TEST_DEMO_PASSWORD}
    )
    unknown = client_a.post(
        "/api/auth/login", json={"username": "kimse.yok", "password": TEST_DEMO_PASSWORD}
    )
    assert existing.status_code == unknown.status_code == 429
    assert existing.json() == unknown.json() == TOO_MANY
    assert existing.headers["retry-after"] == unknown.headers["retry-after"] == str(15 * 60 - 30)


def test_ip_limit_is_per_client_and_ignores_forwarded_header(
    settings: Settings, clock: FakeClock
) -> None:
    with _client_at(settings, clock, "10.0.0.1") as attacker:
        for i in range(20):
            response = attacker.post(
                "/api/auth/login",
                json={"username": f"user{i}", "password": "yanlis parola denemesi"},
                headers={"X-Forwarded-For": f"192.168.0.{i}"},  # never trusted
            )
            assert response.status_code == 401
        blocked = attacker.post(
            "/api/auth/login",
            json={"username": "zeynep.sahin", "password": TEST_DEMO_PASSWORD},
            headers={"X-Forwarded-For": "203.0.113.7"},
        )
        assert blocked.status_code == 429
        assert blocked.json() == TOO_MANY
    with _client_at(settings, clock, "10.0.0.2") as other:
        allowed = other.post(
            "/api/auth/login", json={"username": "zeynep.sahin", "password": TEST_DEMO_PASSWORD}
        )
        assert allowed.status_code == 200


def test_lock_survives_restart(settings: Settings, clock: FakeClock) -> None:
    with _client_at(settings, clock, "10.0.0.1") as first:
        _wrong(first)
    with _client_at(settings, clock, "10.0.0.3") as after_restart:
        response = after_restart.post(
            "/api/auth/login", json={"username": "ali.demir", "password": TEST_DEMO_PASSWORD}
        )
    assert response.status_code == 429


def test_old_attempt_records_are_purged(
    client_a: TestClient, clock: FakeClock, settings: Settings
) -> None:
    _wrong(client_a)
    clock.advance(timedelta(minutes=16))
    assert _login(client_a, "zeynep.sahin", TEST_DEMO_PASSWORD).status_code == 200
    conn = sqlite3.connect(settings.db_path)
    try:
        failures = conn.execute("SELECT COUNT(*) FROM login_failures").fetchone()[0]
        locks = conn.execute("SELECT COUNT(*) FROM account_locks").fetchone()[0]
    finally:
        conn.close()
    assert (failures, locks) == (0, 0)


def test_lock_keeps_existing_session(settings: Settings, clock: FakeClock) -> None:
    with _client_at(settings, clock, "10.0.0.5") as owner:
        assert _login(owner, "ali.demir", TEST_DEMO_PASSWORD).status_code == 200
        with _client_at(settings, clock, "10.0.0.6") as attacker:
            _wrong(attacker)
            assert _login(attacker, "ali.demir", TEST_DEMO_PASSWORD).status_code == 429
        me = owner.get("/api/me")
        assert me.status_code == 200
        assert me.json()["username"] == "ali.demir"


def test_no_password_in_logs_during_lockout(
    client_a: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.DEBUG):
        _wrong(client_a)
        client_a.post(
            "/api/auth/login", json={"username": "ali.demir", "password": TEST_DEMO_PASSWORD}
        )
    text = caplog.text
    assert "account locked username=ali.demir ip=10.0.0.1" in text
    assert "yanlis parola denemesi" not in text
    assert TEST_DEMO_PASSWORD not in text
