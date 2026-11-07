-- Users (spec 0002). username is unique case-insensitively; the top manager has no manager.
CREATE TABLE users (
    id            INTEGER PRIMARY KEY,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    full_name     TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('EMPLOYEE', 'MANAGER')),
    manager_id    INTEGER REFERENCES users (id),
    password_hash TEXT    NOT NULL
);

-- Server-side sessions: only the SHA-256 digest of the browser token is stored.
-- Timestamps are UTC ISO-8601 with a Z suffix.
CREATE TABLE sessions (
    token_hash   TEXT    PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users (id),
    created_at   TEXT    NOT NULL,
    last_seen_at TEXT    NOT NULL
);

CREATE INDEX sessions_user_id ON sessions (user_id);
