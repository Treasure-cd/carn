from carn.models import Package
from carn.scanners.base import Scanner, run

_COLUMNS = "application,name,version,branch,description"


class FlatpakScanner(Scanner):
    name = "flatpak"
    binary = "flatpak"
    install_template = "flatpak install {name}"

    def scan(self) -> list[Package]:
        apps = set(run(["flatpak", "list", "--app", "--columns=application"]).split())
        raw = run(["flatpak", "list", f"--columns={_COLUMNS}"])
        return [p for line in raw.splitlines() if (p := self._parse(line, apps))]

    @staticmethod
    def _parse(line: str, apps: set[str]) -> Package | None:
        parts = line.split("\t")
        if len(parts) != 5:
            return None
        app_id, human, version, branch, desc = parts
        if "." not in app_id:
            return None
        return Package(
            source="flatpak",
            name=app_id,
            version=version or branch,
            summary=f"{human}: {desc}" if desc else human,
            manual=app_id in apps,
        )


if __name__ == "__main__":
    pkgs = FlatpakScanner().scan()
    print(f"{len(pkgs)} flatpaks, {sum(bool(p.manual) for p in pkgs)} apps\n")
    for p in pkgs:
        print(f"{'*' if p.manual else ' '} {p.name:40} {p.version:15} {p.summary[:40]}")
