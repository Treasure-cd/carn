import sqlite3
from datetime import datetime, timezone

from carn.models import Package

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
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
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
