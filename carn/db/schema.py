import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".local" / "share" / "carn" / "carn.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS packages (
    source      TEXT NOT NULL,          -- apt, snap, etc
    name        TEXT NOT NULL,
    version     TEXT,
    summary     TEXT,
    homepage    TEXT,
    size_kb     INTEGER,
    manual      INTEGER,                -- 1 or 0 or NULL (unknown)
    baseline    INTEGER,                -- 1 is shipped with the OS, NULL is not checked yet
    section     TEXT,                   -- apt only for now
    install_date TEXT,                  -- YYYY-MM-DD, best effort, NULL if unknown
    first_seen  TEXT NOT NULL,          -- when carn first saw it
    last_seen   TEXT NOT NULL,
    removed_at  TEXT,                   -- it's NULL if it's still installed
    PRIMARY KEY (source, name)
);

CREATE TABLE IF NOT EXISTS annotations (
    source      TEXT NOT NULL,
    name        TEXT NOT NULL,
    note        TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (source, name)
);

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_packages (
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source      TEXT NOT NULL,
    name        TEXT NOT NULL,
    PRIMARY KEY (project_id, source, name)
);
"""


_NEW_COLUMNS = {"section": "TEXT", "install_date": "TEXT"}


def _migrate(conn: sqlite3.Connection) -> None:
    have = {r["name"] for r in conn.execute("PRAGMA table_info(packages)")}
    for col, typ in _NEW_COLUMNS.items():
        if col not in have:
            conn.execute(f"ALTER TABLE packages ADD COLUMN {col} {typ}")
    conn.commit()


def connect(path: str | Path = DB_PATH) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn
