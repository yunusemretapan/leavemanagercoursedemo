from pathlib import Path

from app.config import DEFAULT_DB_PATH, Settings

NO_ENV_FILE = {"LEAVE_ENV_FILE": "does-not-exist.env"}


def test_settings_default_to_localhost_8000() -> None:
    settings = Settings.from_env(NO_ENV_FILE)
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.db_path == DEFAULT_DB_PATH


def test_settings_read_host_port_and_db_path_from_env() -> None:
    settings = Settings.from_env(
        {**NO_ENV_FILE, "LEAVE_HOST": "10.0.0.5", "LEAVE_PORT": "9123", "LEAVE_DB_PATH": "x/y.db"}
    )
    assert settings.host == "10.0.0.5"
    assert settings.port == 9123
    assert settings.db_path == Path("x/y.db")


def test_demo_password_and_cookie_flag_from_env_then_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEMO_PASSWORD=dosyadan gelen parola\nLEAVE_COOKIE_SECURE=true\n", encoding="utf-8"
    )
    from_file = Settings.from_env({"LEAVE_ENV_FILE": str(env_file)})
    assert from_file.demo_password == "dosyadan gelen parola"  # noqa: S105 — fictional
    assert from_file.cookie_secure is True
    from_env = Settings.from_env(
        {"LEAVE_ENV_FILE": str(env_file), "DEMO_PASSWORD": "ortamdan gelen parola"}
    )
    assert from_env.demo_password == "ortamdan gelen parola"  # noqa: S105 — env wins


def test_defaults_have_no_demo_password_and_insecure_cookie_off() -> None:
    settings = Settings.from_env(NO_ENV_FILE)
    assert settings.demo_password is None
    assert settings.cookie_secure is False
