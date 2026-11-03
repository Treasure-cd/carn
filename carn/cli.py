import argparse
import sqlite3

from carn.db.queries import list_packages
from carn.db.schema import connect
from carn.db.store import annotate
from carn.sync import ALL_SCANNERS, sync_all


def cmd_sync(args: argparse.Namespace, conn: sqlite3.Connection) -> None:
    for source, status in sync_all(conn).items():
        print(f"{source:8} {status}")


def cmd_list(args: argparse.Namespace, conn: sqlite3.Connection) -> None:
    rows = list_packages(
        conn, source=args.source, show_all=args.all, search=args.search
    )
    if not rows:
        print("nothing found")
        return
    width = max(len(r["name"]) for r in rows)
    for r in rows:
        desc = f"> {r['note']}" if r["note"] else (r["summary"] or "")
        print(f"{r['source']:6} {r['name']:{width}}  {desc[:70]}")
    print(f"\n{len(rows)} packages")


def cmd_note(args: argparse.Namespace, conn: sqlite3.Connection) -> None:
    known = conn.execute(
        "SELECT 1 FROM packages WHERE source = ? AND name = ?",
        (args.source, args.name),
    ).fetchone()
    annotate(conn, args.source, args.name, " ".join(args.note))
    if known:
        print("saved")
    else:
        print(f"saved, but {args.source}/{args.name} isn't in the scanned packages (typo?)")


def main(argv: list[str] | None = None) -> None:
    sources = [s.name for s in ALL_SCANNERS]
    parser = argparse.ArgumentParser(prog="carn", description="Track what you installed, and why.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("sync", help="scan package managers into the db")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("list", help="show packages (default: ones you installed yourself)")
    p.add_argument("search", nargs="?", help="match name, summary or note")
    p.add_argument("-a", "--all", action="store_true", help="include base-system packages")
    p.add_argument("-s", "--source", choices=sources)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("note", help="write down why you installed something")
    p.add_argument("source", choices=sources)
    p.add_argument("name")
    p.add_argument("note", nargs="+", help="the note (quotes optional)")
    p.set_defaults(func=cmd_note)

    args = parser.parse_args(argv)
    args.func(args, connect())
