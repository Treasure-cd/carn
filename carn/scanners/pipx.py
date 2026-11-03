import json

from carn.models import Package
from carn.scanners.base import Scanner, ScannerError, run


class PipxScanner(Scanner):
    name = "pipx"
    binary = "pipx"

    def scan(self) -> list[Package]:
        raw = run(["pipx", "list", "--json"])
        try:
            venvs = json.loads(raw)["venvs"]
        except (json.JSONDecodeError, KeyError) as e:
            raise ScannerError(f"unexpected pipx output: {e}")

        packages = []
        for venv_name, venv in venvs.items():
            main = venv.get("metadata", {}).get("main_package", {})
            apps = main.get("apps", [])
            packages.append(
                Package(
                    source="pipx",
                    name=main.get("package", venv_name),
                    version=main.get("package_version", ""),
                    summary=f"commands: {', '.join(apps)}" if apps else "",
                    manual=True,   # pipx only installs what you ask it to
                )
            )
        return packages


if __name__ == "__main__":
    pkgs = PipxScanner().scan()
    print(f"{len(pkgs)} pipx packages\n")
    for p in pkgs:
        print(f"{p.name:30} {p.version:12} {p.summary}")
