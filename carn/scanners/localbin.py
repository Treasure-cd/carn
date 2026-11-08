import os
from pathlib import Path

from carn.models import Package
from carn.scanners.base import Scanner, mtime_date, tilde

BIN_DIR = Path.home() / ".local" / "bin"

# symlinks pointing into these are already covered by another scanner
_MANAGED = [
    Path.home() / ".local" / "share" / "pipx",
    Path.home() / ".local" / "pipx",
    Path.home() / ".local" / "share" / "uv" / "tools",
]


def _is_managed(target: Path) -> bool:
    return any(target.is_relative_to(m) for m in _MANAGED)


def _kind(path: Path) -> str:
    """Say what a file is, from its first bytes."""
    try:
        with open(path, "rb") as f:
            head = f.read(128)
    except OSError:
        return "file"
    if head.startswith(b"\x7fELF"):
        return "binary"
    if head.startswith(b"#!"):
        tokens = head.split(b"\n", 1)[0][2:].decode(errors="replace").split()
        if not tokens:
            return "script"
        if tokens[0].endswith("/env"):   # "#!/usr/bin/env python3"
            interp = next((t for t in tokens[1:] if not t.startswith("-")), "env")
        else:
            interp = Path(tokens[0]).name
        return f"script ({interp})"
    return "file"


class LocalBinScanner(Scanner):
    name = "bin"
    binary = ""
    install_template = ""

    def available(self) -> bool:
        return BIN_DIR.is_dir()

    def scan(self) -> list[Package]:
        pkgs = []
        for path in sorted(BIN_DIR.iterdir()):
            try:
                real = Path(os.path.realpath(path))
                if not real.is_file() or not os.access(real, os.X_OK):
                    continue
                if _is_managed(real) or real.name.lower().endswith(".appimage"):
                    continue
                st = path.lstat()
                size = real.stat().st_size
            except OSError:
                continue
            kind = _kind(real)
            summary = f"{kind}, link to {tilde(real)}" if path.is_symlink() else kind
            pkgs.append(Package(
                source="bin",
                name=path.name,
                version="",
                summary=summary,
                size_kb=size // 1024,
                baseline=False,
                manual=True,
                install_date=mtime_date(st),
            ))
        return pkgs


if __name__ == "__main__":
    pkgs = LocalBinScanner().scan()
    print(f"{len(pkgs)} files in {BIN_DIR}\n")
    for p in pkgs:
        print(f"{p.name:30} {p.summary}")
