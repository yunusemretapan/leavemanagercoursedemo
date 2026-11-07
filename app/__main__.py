"""Start the application: python -m app (README.md, Çalıştırma)."""

import sys

import uvicorn

from app.config import Settings
from app.main import create_app
from app.models.errors import ConfigurationError

EXIT_CONFIGURATION_ERROR = 2


def main() -> None:
    settings = Settings.from_env()
    try:
        app = create_app(settings)
    except ConfigurationError as exc:
        # The reason only; the configured password is never printed (spec 0002 R-3).
        print(f"Leave Manager başlatılamadı: {exc}", file=sys.stderr)
        sys.exit(EXIT_CONFIGURATION_ERROR)
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
