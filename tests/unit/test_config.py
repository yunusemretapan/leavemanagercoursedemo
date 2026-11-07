from pathlib import Path

from app.config import DEFAULT_DB_PATH, Settings


def test_settings_default_to_localhost_8000() -> None:
    settings = Settings.from_env({})
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.db_path == DEFAULT_DB_PATH


def test_settings_read_host_port_and_db_path_from_env() -> None:
    settings = Settings.from_env(
        {"LEAVE_HOST": "10.0.0.5", "LEAVE_PORT": "9123", "LEAVE_DB_PATH": "x/y.db"}
    )
    assert settings.host == "10.0.0.5"
    assert settings.port == 9123
    assert settings.db_path == Path("x/y.db")
