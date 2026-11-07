-- Application metadata (key/value). Not a business table; gives the walking skeleton a real schema.
CREATE TABLE app_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
