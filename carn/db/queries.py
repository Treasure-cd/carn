import sqlite3


def list_packages(
    conn: sqlite3.Connection,
    *,
    source: str | None = None,
    show_all: bool = False,
    search: str | None = None,
    include_removed: bool = False,
) -> list[sqlite3.Row]:
    where = ["p.manual = 1"]
    params: list[str] = []

    if not show_all:
        where.append("p.baseline IS NOT 1")   # NULL (unchecked) still counts as yours
    if not include_removed:
        where.append("p.removed_at IS NULL")
    if source:
        where.append("p.source = ?")
        params.append(source)
    if search:
        where.append("(p.name LIKE ? OR p.summary LIKE ? OR a.note LIKE ?)")
        params += [f"%{search}%"] * 3

    sql = f"""
        SELECT p.source, p.name, p.version, p.summary, p.size_kb,
               p.first_seen, p.removed_at, a.note
        FROM packages p
        LEFT JOIN annotations a ON a.source = p.source AND a.name = p.name
        WHERE {' AND '.join(where)}
        ORDER BY p.source, p.name
    """
    return conn.execute(sql, params).fetchall()
