import sqlite3

from carn.db.store import sync_packages
from carn.scanners.apt import AptScanner
from carn.scanners.base import Scanner, ScannerError
from carn.scanners.snap import SnapScanner
from carn.scanners.flatpak import FlatpakScanner
from carn.scanners.pipx import PipxScanner

ALL_SCANNERS: list[Scanner] = [AptScanner(), SnapScanner(), FlatpakScanner(), PipxScanner()]


def sync_all(conn: sqlite3.Connection) -> dict[str, str]:
    """Scan every available source into the db. Returns {source: status}."""
    results: dict[str, str] = {}
    for scanner in ALL_SCANNERS:
        if not scanner.available():
            results[scanner.name] = "skipped (not installed)"
            continue
        try:
            packages = scanner.scan()
        except ScannerError as e:
            results[scanner.name] = f"failed: {e}"
            continue  # we're not syncing after a failed scan
        sync_packages(conn, scanner.name, packages)
        results[scanner.name] = f"{len(packages)} packages"
    return results
