import sqlite3


def list_packages(
    conn: sqlite3.Connection,
    *,
    source: str | None = None,
    show_all: bool = False,
    search: str | None = None,
    include_removed: bool = False,
    annotated_first: bool = False,
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

    order = "(a.note IS NULL), p.source, p.name" if annotated_first else "p.source, p.name"

    sql = f"""
        SELECT p.source, p.name, p.version, p.summary, p.homepage, p.section, p.install_date,
               p.size_kb, p.first_seen, p.removed_at, a.note
        FROM packages p
        LEFT JOIN annotations a ON a.source = p.source AND a.name = p.name
        WHERE {' AND '.join(where)}
        ORDER BY {order}
    """
    return conn.execute(sql, params).fetchall()


def list_annotated(conn: sqlite3.Connection, *, search: str | None = None) -> list[sqlite3.Row]:
    where = ["1 = 1"]
    params: list[str] = []
    if search:
        where.append("(a.name LIKE ? OR a.note LIKE ? OR p.summary LIKE ?)")
        params += [f"%{search}%"] * 3

    sql = f"""
        SELECT a.source, a.name, a.note, a.updated_at, p.summary, p.removed_at
        FROM annotations a
        LEFT JOIN packages p ON p.source = a.source AND p.name = a.name
        WHERE {' AND '.join(where)}
        ORDER BY a.updated_at DESC
    """
    return conn.execute(sql, params).fetchall()


def list_projects(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("""
        SELECT p.id, p.name, p.description, COUNT(pp.name) AS n
        FROM projects p
        LEFT JOIN project_packages pp ON pp.project_id = p.id
        GROUP BY p.id
        ORDER BY p.name COLLATE NOCASE
    """).fetchall()

def list_project_packages(conn: sqlite3.Connection, project_id: int) -> list[sqlite3.Row]:
    return conn.execute("""
        SELECT pp.source, pp.name, k.summary, k.removed_at
        FROM project_packages pp
        LEFT JOIN packages k ON k.source = pp.source AND k.name = pp.name
        WHERE pp.project_id = ?
        ORDER BY pp.source, pp.name
    """, (project_id,)).fetchall()


def projects_for_package(conn: sqlite3.Connection, source: str, name: str) -> list[str]:
    rows = conn.execute("""
        SELECT p.name FROM projects p
        JOIN project_packages pp ON pp.project_id = p.id
        WHERE pp.source = ? AND pp.name = ?
        ORDER BY p.name COLLATE NOCASE
    """, (source, name)).fetchall()
    return [r["name"] for r in rows]
