"""Ordered, numbered SQL migrations (docs/conventions.md, Data rules).

Each ``NNNN_<name>.sql`` runs once, in its own transaction together with its bookkeeping row;
an applied migration is never run again.
"""

from pathlib import Path

from app.data.database import Database

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def apply_migrations(db: Database, directory: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply every migration not yet recorded; return the versions applied now."""
    db.path.parent.mkdir(parents=True, exist_ok=True)
    with db.connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)")
        conn.commit()
    applied_now: list[str] = []
    for script in sorted(directory.glob("[0-9][0-9][0-9][0-9]_*.sql")):
        version = script.stem
        with db.connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?", (version,)
            ).fetchone()
            if row is not None:
                continue
            # autocommit=False: executescript runs inside the open transaction (no implicit COMMIT)
            conn.executescript(script.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
        applied_now.append(version)
    return applied_now
