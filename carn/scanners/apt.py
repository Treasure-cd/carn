from carn.models import Package
from carn.scanners.base import Scanner, run
from datetime import datetime, timedelta
import glob
import gzip
import os
import re

_INSTALL_EVENT = re.compile(r"(\S+ \S+) install (\S+?)(?::\w+)? ")
BASELINE_WINDOW = timedelta(hours=24)


def _first_installs() -> dict[str, datetime]:
    """Packages first installed within 24h of the oldest dpkg log event."""
    first: dict[str, datetime] = {}
    for path in glob.glob("/var/log/dpkg.log*"):
        opener = gzip.open if path.endswith(".gz") else open
        try:
            with opener(path, "rt", errors="replace") as f:
                for line in f:
                    m = _INSTALL_EVENT.match(line)
                    if not m:
                        continue
                    ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                    name = m.group(2)
                    if name not in first or ts < first[name]:
                        first[name] = ts
        except OSError:
            continue
    return first


def _baseline_names(first: dict[str, datetime]) -> set[str] | None:
    """Packages first installed within 24h of the oldest dpkg log event."""
    if not first:
        return None
    cutoff = min(first.values()) + BASELINE_WINDOW
    return {n for n, ts in first.items() if ts <= cutoff}


def _list_mtime(base: str) -> datetime | None:
    """Fallback date: when dpkg last unpacked the package (so it moves on upgrades)."""
    paths = [f"/var/lib/dpkg/info/{base}.list"] or []
    paths += glob.glob(f"/var/lib/dpkg/info/{base}:*.list")
    for path in paths:
        try:
            return datetime.fromtimestamp(os.path.getmtime(path))
        except OSError:
            continue
    return None

# one line per package, tab-separated
_FORMAT = (
    "${Package}\t${Version}\t${Installed-Size}\t"
    "${Homepage}\t${db:Status-Abbrev}\t${binary:Summary}\t${Section}\n"
)


class AptScanner(Scanner):
    name = "apt"
    binary = "dpkg-query"
    install_template = "sudo apt install {name}"

    def scan(self) -> list[Package]:
        manual = self._manual_names()
        first = _first_installs()
        baseline = _baseline_names(first)
        raw = run(["dpkg-query", "-W", "-f", _FORMAT])
        return [p for line in raw.splitlines() if (p := self._parse(line, manual, baseline, first))]

    def _manual_names(self) -> set[str]:
        return set(run(["apt-mark", "showmanual"]).split())

    @staticmethod
    def _parse(line: str, manual: set[str], baseline: set[str] | None,
               first: dict[str, datetime]) -> Package | None:
        parts = line.split("\t")
        if len(parts) != 7:
            return None
        name, version, size, homepage, status, summary, section = parts
        if not status.startswith("ii"):  # skip removed/config only leftovers
            return None
        base = name.split(":")[0]
        when = first.get(base) or _list_mtime(base)
        return Package(
            source="apt",
            name=name,
            version=version,
            summary=summary,
            homepage=homepage,
            size_kb=int(size) if size.isdigit() else None,
            manual=base in manual or name in manual,
            baseline=None if baseline is None else base in baseline,
            section=section.rsplit("/", 1)[-1],   # Ubuntu writes "universe/devel"
            install_date=when.strftime("%Y-%m-%d") if when else None,
        )


if __name__ == "__main__":
    pkgs = AptScanner().scan()
    manual = [p for p in pkgs if p.manual]
    print(f"{len(pkgs)} installed, {len(manual)} manually installed\n")
    for p in manual:
        print(f"{p.name:30} {p.version:20} {p.summary[:50]}")
