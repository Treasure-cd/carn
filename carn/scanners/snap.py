import json
import re
from carn.models import Package
from carn.scanners.base import Scanner, ScannerError, run
from pathlib import Path

SEED_FILE = Path("/var/lib/snapd/seed/seed.yaml")


def _seed_names() -> set[str] | None:
    try:
        text = SEED_FILE.read_text()
    except OSError:
        return None  # None = "couldn't check", which is different from "empty"
    return set(re.findall(r"^\s*name:\s*(\S+)", text, re.M))


class SnapScanner(Scanner):
    name = "snap"
    binary = "snap"
    install_template = "sudo snap install {name}"

    def scan(self) -> list[Package]:
        raw = run(["snap", "debug", "api", "/v2/snaps"])
        try:
            snaps = json.loads(raw)["result"]
        except (json.JSONDecodeError, KeyError) as e:
            raise ScannerError(f"unexpected snapd response: {e}")
        seed = _seed_names()
        return [self._parse(s, seed) for s in snaps]

    @staticmethod
    def _parse(s: dict, seed: set[str] | None) -> Package:
        size = s.get("installed-size")          # bytes
        return Package(
            source="snap",
            name=s["name"],
            version=s.get("version", ""),
            summary=s.get("summary", ""),
            homepage=s.get("website") or "",
            size_kb=size // 1024 if isinstance(size, int) else None,
            baseline=None if seed is None else s["name"] in seed,
            manual=s.get("type") == "app" and bool(s.get("apps")) and not s["name"].startswith("mesa-"),
            install_date=(s.get("install-date") or "")[:10] or None,
        )


if __name__ == "__main__":
    pkgs = SnapScanner().scan()
    print(f"{len(pkgs)} snaps, {sum(bool(p.manual) for p in pkgs)} look manual\n")
    for p in pkgs:
        print(f"{'*' if p.manual else ' '} {p.name:30} {p.version:20} {p.size_kb} KB")
