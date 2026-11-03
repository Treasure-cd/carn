from carn.models import Package
from carn.scanners.base import Scanner, run

# one line per package, tab-separated
_FORMAT = (
    "${Package}\t${Version}\t${Installed-Size}\t"
    "${Homepage}\t${db:Status-Abbrev}\t${binary:Summary}\n"
)


class AptScanner(Scanner):
    name = "apt"
    binary = "dpkg-query"

    def scan(self) -> list[Package]:
        manual = self._manual_names()
        raw = run(["dpkg-query", "-W", "-f", _FORMAT])
        return [p for line in raw.splitlines() if (p := self._parse(line, manual))]

    def _manual_names(self) -> set[str]:
        return set(run(["apt-mark", "showmanual"]).split())

    @staticmethod
    def _parse(line: str, manual: set[str]) -> Package | None:
        parts = line.split("\t")
        if len(parts) != 6:
            return None
        name, version, size, homepage, status, summary = parts
        if not status.startswith("ii"): # skip removed/config only leftovers
            return None
        base = name.split(":")[0]
        return Package(
            source="apt",
            name=name,
            version=version,
            summary=summary,
            homepage=homepage,
            size_kb=int(size) if size.isdigit() else None,
            manual=base in manual or name in manual,
        )


if __name__ == "__main__":
    pkgs = AptScanner().scan()
    manual = [p for p in pkgs if p.manual]
    print(f"{len(pkgs)} installed, {len(manual)} manually installed\n")
    for p in manual:
        print(f"{p.name:30} {p.version:20} {p.summary[:50]}")
