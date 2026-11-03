import sqlite3
from datetime import datetime, timezone

from carn.models import Package

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

_UPSERT = """
INSERT INTO packages
    (source, name, version, summary, homepage, size_kb, manual, baseline, first_seen, last_seen)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(source, name) DO UPDATE SET
    version    = excluded.version,
    summary    = excluded.summary,
    homepage   = excluded.homepage,
    size_kb    = excluded.size_kb,
    manual     = excluded.manual,
    baseline   = COALESCE(packages.baseline, excluded.baseline),
    last_seen  = excluded.last_seen,
    removed_at = NULL
"""


def sync_packages(conn: sqlite3.Connection, source: str, packages: list[Package]) -> None:
    now = _now()
    rows = [
        (
            p.source, p.name, p.version, p.summary, p.homepage, p.size_kb,
            None if p.manual is None else int(p.manual),
            None if p.baseline is None else int(p.baseline),
            now, now,
        )
        for p in packages
    ]
    with conn:
        conn.execute(
            "UPDATE packages SET removed_at = ? WHERE source = ? AND removed_at IS NULL",
            (now, source),
        )
        conn.executemany(_UPSERT, rows)

def annotate(conn: sqlite3.Connection, source: str, name: str, note: str) -> None:
    """Set (or overwrite) the note for a package."""
    with conn:
        conn.execute(
            """
            INSERT INTO annotations (source, name, note, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(source, name) DO UPDATE SET
                note       = excluded.note,
                updated_at = excluded.updated_at
            """,
            (source, name, note, _now()),
        )
