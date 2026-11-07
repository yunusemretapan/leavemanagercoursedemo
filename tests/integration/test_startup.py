import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from app.config import REPO_ROOT

pytestmark = pytest.mark.integration

STARTUP_BUDGET_SECONDS = 10.0
# A non-default loopback address: if the app ignored LEAVE_HOST and bound 127.0.0.1, the probe
# below would fail. 127.0.0.0/8 is loopback on Linux (CI) and Windows.
TEST_HOST = "127.0.0.2"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((TEST_HOST, 0))
        port: int = sock.getsockname()[1]
        return port


def test_app_starts_and_answers_health_on_configured_port(tmp_path: Path) -> None:
    port = _free_port()
    env = {
        **os.environ,
        "LEAVE_HOST": TEST_HOST,
        "LEAVE_PORT": str(port),
        "LEAVE_DB_PATH": str(tmp_path / "start.db"),
        "LEAVE_ENV_FILE": str(tmp_path / "no.env"),
        "DEMO_PASSWORD": "kurs demosu baslangic parolasi",
    }
    # The documented start command (README.md, Çalıştırma), run with this venv's interpreter.
    process = subprocess.Popen(
        [sys.executable, "-m", "app"],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + STARTUP_BUDGET_SECONDS
        status = None
        while time.monotonic() < deadline:
            try:
                status = httpx.get(f"http://{TEST_HOST}:{port}/api/health", timeout=1).status_code
                if status == 200:
                    break
            except httpx.TransportError:
                pass
            time.sleep(0.2)
        assert status == 200, f"health not ok within {STARTUP_BUDGET_SECONDS}s"
    finally:
        # Resource hygiene: the app under test never outlives the test, also on failure.
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.mark.parametrize(
    ("demo_password", "expected_reason"),
    [
        (None, "DEMO_PASSWORD tanımlı değil"),
        ("kisa", "en az 12 karakter"),
        ("parola123456", "yaygın kullanılan"),
    ],
)
def test_app_refuses_to_start_without_valid_demo_password(
    tmp_path: Path, demo_password: str | None, expected_reason: str
) -> None:
    env = {k: v for k, v in os.environ.items() if k != "DEMO_PASSWORD"}
    env.update(
        LEAVE_PORT=str(_free_port()),
        LEAVE_DB_PATH=str(tmp_path / "refuse.db"),
        LEAVE_ENV_FILE=str(tmp_path / "no.env"),
        PYTHONIOENCODING="utf-8",
    )
    if demo_password is not None:
        env["DEMO_PASSWORD"] = demo_password
    completed = subprocess.run(
        [sys.executable, "-m", "app"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        timeout=30,
        check=False,
    )
    stderr = completed.stderr.decode("utf-8")
    assert completed.returncode == 2
    assert expected_reason in stderr
    if demo_password is not None:
        assert demo_password not in stderr
