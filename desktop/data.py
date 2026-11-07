from contextlib import closing

from nicegui import run

from carn.db import queries, store
from carn.db.schema import connect
from carn.sync import ALL_SCANNERS, sync_all

SOURCES = [s.name for s in ALL_SCANNERS]
_TEMPLATES = {s.name: s.install_template for s in ALL_SCANNERS}


def install_cmd(source: str, name: str) -> str:
    template = _TEMPLATES.get(source, '')
    return template.format(name=name) if template else ''


def installed(*, search=None, source=None, show_all=False) -> list[dict]:
    with closing(connect()) as conn:
        rows = queries.list_packages(
            conn,
            source=source or None,
            show_all=show_all,
            search=search or None,
            annotated_first=True,
        )
        return [dict(r) for r in rows]


def notes(*, search=None) -> list[dict]:
    with closing(connect()) as conn:
        return [dict(r) for r in queries.list_annotated(conn, search=search or None)]


def find_packages(search: str) -> list[dict]:
    """For the Add note picker: any scanned package, baseline included."""
    with closing(connect()) as conn:
        rows = queries.list_packages(conn, show_all=True, search=search or None)
        return [dict(r) for r in rows]


def save_note(source: str, name: str, note: str) -> None:
    with closing(connect()) as conn:
        store.annotate(conn, source, name, note)


def delete_note(source: str, name: str) -> None:
    with closing(connect()) as conn:
        store.delete_annotation(conn, source, name)


def _sync() -> dict[str, str]:
    with closing(connect()) as conn:   # opened inside the worker thread
        return sync_all(conn)


async def sync() -> dict[str, str]:
    return await run.io_bound(_sync)


def projects() -> list[dict]:
    with closing(connect()) as conn:
        return [dict(r) for r in queries.list_projects(conn)]


def project_packages(project_id: int) -> list[dict]:
    with closing(connect()) as conn:
        return [dict(r) for r in queries.list_project_packages(conn, project_id)]


def projects_of(source: str, name: str) -> list[str]:
    with closing(connect()) as conn:
        return queries.projects_for_package(conn, source, name)


def create_project(name: str, description: str = '') -> int:
    with closing(connect()) as conn:
        return store.create_project(conn, name, description)


def update_project(project_id: int, name: str, description: str) -> None:
    with closing(connect()) as conn:
        store.update_project(conn, project_id, name, description)


def delete_project(project_id: int) -> None:
    with closing(connect()) as conn:
        store.delete_project(conn, project_id)


def add_to_project(project_id: int, source: str, name: str) -> None:
    with closing(connect()) as conn:
        store.add_to_project(conn, project_id, source, name)


def remove_from_project(project_id: int, source: str, name: str) -> None:
    with closing(connect()) as conn:
        store.remove_from_project(conn, project_id, source, name)
