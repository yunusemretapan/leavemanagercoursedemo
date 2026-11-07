"""Runtime settings from environment variables (README.md, Çalıştırma)."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_DB_PATH = REPO_ROOT / "data" / "leavemanager.db"


@dataclass(frozen=True)
class Settings:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    db_path: Path = DEFAULT_DB_PATH

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        source = os.environ if env is None else env
        return cls(
            host=source.get("LEAVE_HOST", DEFAULT_HOST),
            port=int(source.get("LEAVE_PORT", str(DEFAULT_PORT))),
            db_path=Path(source.get("LEAVE_DB_PATH", str(DEFAULT_DB_PATH))),
        )
