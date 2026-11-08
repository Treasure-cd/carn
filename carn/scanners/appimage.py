import re
from pathlib import Path

from carn.models import Package
from carn.scanners.base import Scanner, mtime_date, tilde

HOME = Path.home()
# AppImages have no standard home, so check the usual places (not recursive)
SEARCH_DIRS = [
    HOME / "Applications", HOME / "AppImages", HOME / ".local" / "bin",
    HOME / "Downloads", HOME / "Desktop", Path("/opt"),
]
DESKTOP_DIR = HOME / ".local" / "share" / "applications"

_EXEC = re.compile(r'^Exec=(?:"([^"]+\.appimage)"|(\S+\.appimage))', re.I | re.M)
_ARCH = re.compile(r"[-_.](?:x86_64|amd64|x64|aarch64|arm64|i386|linux)(?=[-_.]|$)", re.I)


def _split(filename: str) -> tuple[str, str]:
    """'Cursor-0.42.3-x86_64.AppImage' -> ('Cursor', '0.42.3'). A heuristic."""
    stem = _ARCH.sub("", re.sub(r"\.appimage$", "", filename, flags=re.I))
    parts = re.split(r"[-_ ]v?(?=\d)", stem, maxsplit=1)
    name = parts[0] or stem
    return name, parts[1] if len(parts) > 1 else ""


def _from_desktop_entries() -> list[Path]:
    """AppImages that were integrated into the app menu, wherever they live."""
    found: list[Path] = []
    if not DESKTOP_DIR.is_dir():
        return found
    for entry in DESKTOP_DIR.glob("*.desktop"):
        try:
            text = entry.read_text(errors="replace")
        except OSError:
            continue
        found += [Path(m.group(1) or m.group(2)) for m in _EXEC.finditer(text)]
    return found


def _candidates() -> list[Path]:
    paths: list[Path] = []
    for d in SEARCH_DIRS:
        try:
            paths += [p for p in d.iterdir() if p.name.lower().endswith(".appimage")]
        except OSError:
            continue
    paths += _from_desktop_entries()
    unique: dict[str, Path] = {}
    for p in paths:
        real = p.resolve()
        if real.is_file():
            unique[str(real)] = real
    return list(unique.values())


class AppImageScanner(Scanner):
    name = "appimage"
    binary = ""
    install_template = ""

    def available(self) -> bool:
        return True

    def scan(self) -> list[Package]:
        best: dict[str, tuple[float, Package]] = {}
        for real in _candidates():
            try:
                st = real.stat()
            except OSError:
                continue
            name, version = _split(real.name)
            pkg = Package(
                source="appimage",
                name=name,
                version=version,
                summary=f"AppImage in {tilde(real.parent)}",
                size_kb=st.st_size // 1024,
                baseline=False,
                manual=True,
                install_date=mtime_date(st),
            )
            if name not in best or st.st_mtime > best[name][0]:   # newest version wins
                best[name] = (st.st_mtime, pkg)
        return sorted((p for _, p in best.values()), key=lambda p: p.name.lower())


if __name__ == "__main__":
    pkgs = AppImageScanner().scan()
    print(f"{len(pkgs)} AppImages\n")
    for p in pkgs:
        print(f"{p.name:25} {p.version:15} {p.summary}")
