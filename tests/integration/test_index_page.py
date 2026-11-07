import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_index_page_has_lang_heading_and_live_region(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert '<html lang="tr">' in html
    assert html.count("<h1") == 1
    assert "<h1>Leave Manager</h1>" in html
    assert 'aria-live="polite"' in html
