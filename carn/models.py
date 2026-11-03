from dataclasses import dataclass


@dataclass(frozen=True)
class Package:
    source: str # sth like, if it's apt or snap
    name: str
    version: str
    summary: str = "" # one line description, usually comes with the package
    homepage: str = ""
    size_kb: int | None = None
    manual: bool | None = None   # True = you installed it, False = pulled in as a dependency, None = unknown
