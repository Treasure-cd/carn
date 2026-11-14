Data modelling of packages, both regular and annotated (the "extra"). [tick]
Fetching it via CLI (apt, etc underneath), built around core [tick]
Building GUI wrappers around core [tick]
"General" downloads, GUI wrapper around the fetch.
Project creation [tick]
Reverse search around CLI
Description of each package via tldr
Dashboard.


carn/
├── carn/
│   ├── __init__.py
│   ├── models.py            # the Package dataclass (the shared shape)
│   ├── scanners/
│   │   ├── __init__.py      # registry: collects all scanners (later)
│   │   ├── base.py          # Scanner interface + subprocess helper
│   │   ├── apt.py           # <- we start here
│   │   └── snap.py          # <- next
│   └── db/                  # sqlite stuff (later)
