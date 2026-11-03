import shutil
import subprocess
from abc import ABC, abstractmethod

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

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    @abstractmethod
    def scan(self) -> list[Package]:
        ...
