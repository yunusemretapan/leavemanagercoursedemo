import sqlite3
from dataclasses import replace
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

import app.business.auth as auth_module
from app.business import passwords
from app.config import Settings
from app.main import create_app
from tests.conftest import TEST_DEMO_PASSWORD, FakeClock, login

pytestmark = pytest.mark.integration

INVALID = {"error": {"code": "INVALID_CREDENTIALS", "message": "Kullanıcı adı veya parola hatalı."}}


def _set_cookie_header(response_headers: object) -> str:
    headers = response_headers
    values = headers.get_list("set-cookie")  # type: ignore[attr-defined]
    assert len(values) == 1
    return str(values[0]).lower()


def test_login_success_case_insensitive_sets_session_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"username": "ALI.Demir", "password": TEST_DEMO_PASSWORD}
    )
    assert response.status_code == 200
    assert response.json() == {
        "username": "ali.demir",
        "full_name": "Ali Demir",
        "role": "EMPLOYEE",
        "role_label": "Çalışan",
    }
    cookie = _set_cookie_header(response.headers)
    assert cookie.startswith("lm_session=")
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "secure" not in cookie.replace("samesite", "")  # off unless configured
    assert client.get("/api/me").json()["full_name"] == "Ali Demir"


def test_secure_cookie_flag_when_configured(settings: Settings, clock: FakeClock) -> None:
    with TestClient(create_app(replace(settings, cookie_secure=True), clock)) as client:
        response = client.post(
            "/api/auth/login", json={"username": "ali.demir", "password": TEST_DEMO_PASSWORD}
        )
    assert response.status_code == 200
    assert "; secure" in _set_cookie_header(response.headers)


def test_wrong_password_and_unknown_user_get_identical_401(client: TestClient) -> None:
    wrong = client.post(
        "/api/auth/login", json={"username": "ali.demir", "password": TEST_DEMO_PASSWORD + "!"}
    )
    unknown = client.post(
        "/api/auth/login", json={"username": "kimse.yok", "password": TEST_DEMO_PASSWORD}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == INVALID
    assert "set-cookie" not in wrong.headers and "set-cookie" not in unknown.headers


def test_unknown_user_still_verifies_password(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    real_verify = passwords.verify_password

    def spy(password: str, stored: str) -> bool:
        calls.append(stored)
        return real_verify(password, stored)

    monkeypatch.setattr(auth_module, "verify_password", spy)
    response = client.post(
        "/api/auth/login", json={"username": "kimse.yok", "password": TEST_DEMO_PASSWORD}
    )
    assert response.status_code == 401
    assert len(calls) == 1 and calls[0].startswith("scrypt$")


def test_me_without_or_with_tampered_token_is_unauthenticated(client: TestClient) -> None:
    expected = {
        "error": {"code": "UNAUTHENTICATED", "message": "Bu işlem için giriş yapmanız gerekiyor."}
    }
    anonymous = client.get("/api/me")
    assert anonymous.status_code == 401
    assert anonymous.json() == expected

    login(client)
    token = client.cookies.get("lm_session")
    assert token
    client.cookies.set("lm_session", token[:-2] + ("aa" if token[-2:] != "aa" else "bb"))
    tampered = client.get("/api/me")
    assert tampered.status_code == 401
    assert tampered.json() == expected


def test_health_open_and_only_token_hash_stored(client: TestClient, settings: Settings) -> None:
    assert client.get("/api/health").status_code == 200  # no session needed
    login(client)
    token = client.cookies.get("lm_session")
    assert token
    conn = sqlite3.connect(settings.db_path)
    try:
        stored = [row[0] for row in conn.execute("SELECT token_hash FROM sessions")]
    finally:
        conn.close()
    assert stored == [auth_module.token_digest(token)]
    assert token.encode() not in settings.db_path.read_bytes()


def test_expired_session_returns_session_expired_code(client: TestClient, clock: FakeClock) -> None:
    login(client)
    clock.advance(timedelta(minutes=31))
    response = client.get("/api/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_EXPIRED"
    assert client.get("/api/me").json()["error"]["code"] == "UNAUTHENTICATED"  # deleted


def test_logout_ends_session_and_without_session_succeeds(client: TestClient) -> None:
    login(client)
    token = client.cookies.get("lm_session")
    assert client.post("/api/auth/logout", json={}).status_code == 204
    client.cookies.set("lm_session", token or "")
    assert client.get("/api/me").status_code == 401  # old token no longer accepted
    client.cookies.clear()
    assert client.post("/api/auth/logout", json={}).status_code == 204


def test_form_encoded_login_is_rejected_without_session(
    client: TestClient, settings: Settings
) -> None:
    response = client.post(
        "/api/auth/login",
        content=f"username=ali.demir&password={TEST_DEMO_PASSWORD}",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "set-cookie" not in response.headers
    conn = sqlite3.connect(settings.db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
    finally:
        conn.close()


@pytest.mark.parametrize(
    ("content", "content_type"),
    [("", None), ("x=1", "application/x-www-form-urlencoded"), ("{}", "text/plain")],
)
def test_non_json_logout_is_rejected_and_session_survives(
    client: TestClient, content: str, content_type: str | None
) -> None:
    login(client)
    headers = {"Content-Type": content_type} if content_type else {}
    response = client.post("/api/auth/logout", content=content, headers=headers)
    assert response.status_code == 422
    assert "set-cookie" not in response.headers
    assert client.get("/api/me").status_code == 200  # session still alive (CSRF, R-11)


def test_relogin_in_same_browser_invalidates_previous_token(
    client: TestClient, settings: Settings
) -> None:
    login(client)
    old = client.cookies.get("lm_session")
    login(client)  # the browser still sends the old cookie with this login (R-9, fixation)
    new = client.cookies.get("lm_session")
    assert old and new and new != old
    client.cookies.set("lm_session", old)
    stale = client.get("/api/me")
    assert stale.status_code == 401
    assert stale.json()["error"]["code"] == "UNAUTHENTICATED"
    conn = sqlite3.connect(settings.db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1
    finally:
        conn.close()
