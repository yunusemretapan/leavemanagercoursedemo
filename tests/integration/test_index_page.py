import mimetypes

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

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


def test_module_scripts_are_served_as_javascript_even_if_os_says_text_plain(
    settings: Settings,
) -> None:
    # Windows can register .js as text/plain (HKCR\.js); browsers then refuse module scripts and
    # the page never leaves its loading state (VERIFY round 1, F-V1). Force that OS mapping here
    # so this test can turn red on any platform.
    mimetypes.add_type("text/plain", ".js")
    try:
        with TestClient(create_app(settings)) as client:
            response = client.get("/js/main.js")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/javascript")
    finally:
        mimetypes.init()
