import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

pytestmark = pytest.mark.integration


def test_unknown_api_path_returns_standard_404(client: TestClient) -> None:
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "NOT_FOUND", "message": "İstenen kaynak bulunamadı."}
    }


def test_unexpected_error_returns_generic_500_without_internals(settings: Settings) -> None:
    app = create_app(settings)

    # Test-only failing route (spec 0001 constraint: no failing route in production code).
    def boom() -> None:
        raise RuntimeError("secret detail at C:/internal/path.py")

    app.add_api_route("/api/test-boom", boom)
    # Routes match in order and the static mount at "/" is last: move the new route before it.
    app.router.routes.insert(0, app.router.routes.pop())
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/test-boom")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["message"] == (
        "Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin."
    )
    assert "secret" not in response.text
    assert "Traceback" not in response.text
    assert "internal/path" not in response.text
