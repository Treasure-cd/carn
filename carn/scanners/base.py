import shutil
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from carn.models import Package


class ScannerError(Exception):
    pass


def run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        raise ScannerError(f"command not found: {cmd[0]}")
    except subprocess.CalledProcessError as e:
        raise ScannerError(f"{' '.join(cmd)} failed: {e.stderr.strip()}")
    return result.stdout


class Scanner(ABC):
    name: str # Label stored in Package.source
    binary: str # cli it depends on
    install_template: str = ""   # e.g. "sudo apt install {name}"; shown in the GUI

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    @abstractmethod
    def scan(self) -> list[Package]:
        ...


def mtime_date(st) -> str:
    """YYYY-MM-DD from an os.stat result."""
    return datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d")


def tilde(path: Path) -> str:
    """/home/me/x -> ~/x, for display."""
    try:
        return "~/" + str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)
