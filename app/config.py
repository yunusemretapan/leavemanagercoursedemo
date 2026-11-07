"""Runtime settings: environment variables first, then the .env file (README.md, Çalıştırma)."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from starlette.config import Config

from app.business.passwords import PRODUCTION_SCRYPT, ScryptParams

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_DB_PATH = REPO_ROOT / "data" / "leavemanager.db"
DEFAULT_ENV_FILE = REPO_ROOT / ".env"


@dataclass(frozen=True)
class Settings:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    db_path: Path = DEFAULT_DB_PATH
    demo_password: str | None = None
    cookie_secure: bool = False
    # Production cost; changeable only in code (tests), never from the environment (ADR 0001).
    scrypt: ScryptParams = PRODUCTION_SCRYPT

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        source = os.environ if env is None else env
        env_file = Path(source.get("LEAVE_ENV_FILE", str(DEFAULT_ENV_FILE)))
        config = Config(env_file if env_file.is_file() else None, environ=source)
        return cls(
            host=config("LEAVE_HOST", default=DEFAULT_HOST),
            port=config("LEAVE_PORT", cast=int, default=DEFAULT_PORT),
            db_path=Path(config("LEAVE_DB_PATH", default=str(DEFAULT_DB_PATH))),
            demo_password=config("DEMO_PASSWORD", default=None),
            cookie_secure=config("LEAVE_COOKIE_SECURE", cast=bool, default=False),
        )
