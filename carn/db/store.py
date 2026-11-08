import sqlite3
from datetime import datetime, timezone

from carn.models import Package

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

_UPSERT = """
INSERT INTO packages
    (source, name, version, summary, homepage, size_kb, manual, baseline,
     section, install_date, first_seen, last_seen)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(source, name) DO UPDATE SET
    version      = excluded.version,
    summary      = excluded.summary,
    homepage     = excluded.homepage,
    size_kb      = excluded.size_kb,
    manual       = excluded.manual,
    baseline     = COALESCE(packages.baseline, excluded.baseline),
    section      = COALESCE(excluded.section, packages.section),
    install_date = CASE
        WHEN packages.install_date IS NULL OR excluded.install_date < packages.install_date
        THEN excluded.install_date ELSE packages.install_date END,
    last_seen    = excluded.last_seen,
    removed_at   = NULL
"""


def sync_packages(conn: sqlite3.Connection, source: str, packages: list[Package]) -> None:
    now = _now()
    rows = [
        (
            p.source, p.name, p.version, p.summary, p.homepage, p.size_kb,
            None if p.manual is None else int(p.manual),
            None if p.baseline is None else int(p.baseline),
            p.section or None, p.install_date,
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

STATUSES = ("keep", "review", "remove")


def _prune(conn: sqlite3.Connection, source: str, name: str) -> None:
    """Drop the annotation row once it has nothing left in it."""
    conn.execute(
        """
        DELETE FROM annotations
        WHERE source = ? AND name = ? AND note = '' AND status IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM tags t
              WHERE t.source = annotations.source AND t.name = annotations.name
          )
        """,
        (source, name),
    )


def annotate(conn: sqlite3.Connection, source: str, name: str, note: str) -> None:
    """Set (or overwrite) the note (the 'why'). Leaves status and tags untouched."""
    with conn:
        conn.execute(
            """
            INSERT INTO annotations (source, name, note, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(source, name) DO UPDATE SET
                note       = excluded.note,
                updated_at = excluded.updated_at
            """,
            (source, name, note.strip(), _now()),
        )
        _prune(conn, source, name)


def save_annotation(
    conn: sqlite3.Connection, source: str, name: str,
    note: str, status: str | None, tags: list[str],
) -> None:
    """Set note, status and tags together (what the GUI editor saves)."""
    status = status if status in STATUSES else None
    tags = sorted({t.strip().lower().replace(",", " ") for t in tags if t.strip()})
    with conn:
        conn.execute(
            """
            INSERT INTO annotations (source, name, note, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(source, name) DO UPDATE SET
                note       = excluded.note,
                status     = excluded.status,
                updated_at = excluded.updated_at
            """,
            (source, name, note.strip(), status, _now()),
        )
        conn.execute("DELETE FROM tags WHERE source = ? AND name = ?", (source, name))
        conn.executemany(
            "INSERT INTO tags (source, name, tag) VALUES (?, ?, ?)",
            [(source, name, t) for t in tags],
        )
        _prune(conn, source, name)


def delete_annotation(conn: sqlite3.Connection, source: str, name: str) -> None:
    with conn:
        conn.execute("DELETE FROM annotations WHERE source = ? AND name = ?", (source, name))
        conn.execute("DELETE FROM tags WHERE source = ? AND name = ?", (source, name))

def annotate(conn: sqlite3.Connection, source: str, name: str, note: str) -> None:
    """Set (or overwrite) the note (the 'why'). Leaves status and tags untouched."""
    with conn:
        conn.execute(
            """
            INSERT INTO annotations (source, name, note, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(source, name) DO UPDATE SET
                note       = excluded.note,
                updated_at = excluded.updated_at
            """,
            (source, name, note.strip(), _now()),
        )
        _prune(conn, source, name)


def save_annotation(
    conn: sqlite3.Connection, source: str, name: str,
    note: str, status: str | None, tags: list[str],
) -> None:
    """Set note, status and tags together (what the GUI editor saves)."""
    status = status if status in STATUSES else None
    tags = sorted({t.strip().lower().replace(",", " ") for t in tags if t.strip()})
    with conn:
        conn.execute(
            """
            INSERT INTO annotations (source, name, note, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(source, name) DO UPDATE SET
                note       = excluded.note,
                status     = excluded.status,
                updated_at = excluded.updated_at
            """,
            (source, name, note.strip(), status, _now()),
        )
        conn.execute("DELETE FROM tags WHERE source = ? AND name = ?", (source, name))
        conn.executemany(
            "INSERT INTO tags (source, name, tag) VALUES (?, ?, ?)",
            [(source, name, t) for t in tags],
        )
        _prune(conn, source, name)


def delete_annotation(conn: sqlite3.Connection, source: str, name: str) -> None:
    with conn:
        conn.execute("DELETE FROM annotations WHERE source = ? AND name = ?", (source, name))
        conn.execute("DELETE FROM tags WHERE source = ? AND name = ?", (source, name))

def create_project(conn: sqlite3.Connection, name: str, description: str = "") -> int:
    with conn:
        cur = conn.execute(
            "INSERT INTO projects (name, description, created_at) VALUES (?, ?, ?)",
            (name.strip(), description.strip(), _now()),
        )
    return cur.lastrowid


def update_project(conn: sqlite3.Connection, project_id: int, name: str, description: str) -> None:
    with conn:
        conn.execute(
            "UPDATE projects SET name = ?, description = ? WHERE id = ?",
            (name.strip(), description.strip(), project_id),
        )


def delete_project(conn: sqlite3.Connection, project_id: int) -> None:
    with conn:
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))


def add_to_project(conn: sqlite3.Connection, project_id: int, source: str, name: str) -> None:
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO project_packages (project_id, source, name) VALUES (?, ?, ?)",
            (project_id, source, name),
        )


def remove_from_project(conn: sqlite3.Connection, project_id: int, source: str, name: str) -> None:
    with conn:
        conn.execute(
            "DELETE FROM project_packages WHERE project_id = ? AND source = ? AND name = ?",
            (project_id, source, name),
        )
