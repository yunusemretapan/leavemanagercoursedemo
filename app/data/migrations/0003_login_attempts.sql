-- Brute force protection (spec 0003). A failed (or in-flight) login attempt is one row per
-- counter: kind USER keyed by normalised username, kind IP keyed by client address.
-- Timestamps are UTC ISO-8601 with a Z suffix.
CREATE TABLE login_failures (
    id           INTEGER PRIMARY KEY,
    kind         TEXT    NOT NULL CHECK (kind IN ('USER', 'IP')),
    key          TEXT    NOT NULL,
    attempted_at TEXT    NOT NULL
);

CREATE INDEX login_failures_lookup ON login_failures (kind, key, attempted_at);

-- Account locks by normalised username (also for usernames that do not exist: no enumeration).
CREATE TABLE account_locks (
    username     TEXT PRIMARY KEY,
    locked_until TEXT NOT NULL
);
