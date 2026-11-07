import json
import os
from datetime import datetime
from pathlib import Path

from carn.models import Package
from carn.scanners.base import Scanner, ScannerError, run


def _venvs_dir() -> Path | None:
    env = os.environ.get("PIPX_LOCAL_VENVS")
    candidates = [Path(env)] if env else []
    candidates += [Path.home() / ".local/share/pipx/venvs", Path.home() / ".local/pipx/venvs"]
    return next((p for p in candidates if p.is_dir()), None)


def _created(venvs: Path | None, venv_name: str) -> str | None:
    if venvs is None:
        return None
    try:
        ts = (venvs / venv_name / "pyvenv.cfg").stat().st_mtime
    except OSError:
        return None
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


class PipxScanner(Scanner):
    name = "pipx"
    binary = "pipx"
    install_template = "pipx install {name}"

    def scan(self) -> list[Package]:
        raw = run(["pipx", "list", "--json"])
        try:
            venvs = json.loads(raw)["venvs"]
        except (json.JSONDecodeError, KeyError) as e:
            raise ScannerError(f"unexpected pipx output: {e}")

        v_dir = _venvs_dir()
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
                    install_date=_created(v_dir, venv_name),
                )
            )
        return packages


if __name__ == "__main__":
    pkgs = PipxScanner().scan()
    print(f"{len(pkgs)} pipx packages\n")
    for p in pkgs:
        print(f"{p.name:30} {p.version:12} {p.summary}")
