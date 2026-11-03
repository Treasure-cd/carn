# carn

Track what's installed on your Linux machine, and why.

## Usage

Run from the project root:

```bash
python3 -m carn sync                      # scan all package managers into the db
python3 -m carn list                      # software you installed yourself
python3 -m carn list --all                # ...plus base-system packages
python3 -m carn list --source snap        # one source only (-s)
python3 -m carn list docker               # search name, summary and your notes
python3 -m carn note apt docker-ce containers for local dev
```

| Command | What it does |
|---|---|
| `sync` | Runs every available scanner and updates the db. Prints one status line per source. |
| `list [search]` | Shows packages. Default view is things you installed yourself. |
| `list -a / --all` | Includes manual packages that shipped with the OS (the baseline). |
| `list -s / --source` | Filters to one source (`apt`, `snap`, ...). |
| `note <source> <name> <text>` | Saves why you installed something. Overwrites any earlier note. Quotes are optional. |

## How it works

- **Scanners** (`carn/scanners/`) fetch and parse one package manager each into `Package` objects. They know nothing about the db.
- **Core data** (`packages` table) is rewritten on every `sync`. Packages that disappear get a `removed_at` timestamp instead of being deleted.
- **Annotations** (`annotations` table) are your notes. A scan never touches them, so notes survive removing and reinstalling a package.
- **Default view** = `manual = 1` and not `baseline`.
  - `manual`: you installed it, rather than it arriving as a dependency (apt: `apt-mark showmanual`; snap: a heuristic on snap type and apps).
  - `baseline`: it shipped with the OS (apt: first installed within 24h of the oldest `dpkg.log` event; snap: listed in `/var/lib/snapd/seed/seed.yaml`).
- The baseline is stored the first time a package is seen and never recomputed, because dpkg logs rotate (around Feb 2027 on this machine).

## Layout

```
carn/
├── __main__.py        # python3 -m carn
├── cli.py             # argparse commands
├── sync.py            # runs all scanners into the db
├── models.py          # Package dataclass
├── scanners/          # base.py, apt.py, snap.py, ...
└── db/                # schema.py, store.py (writes), queries.py (reads)
```

Run a single scanner to inspect its output: `python3 -m carn.scanners.apt`

The db lives at `~/.local/share/carn/carn.db`.

## Sources

apt, snap

## Ideas / later

- Pin a package into the default view even if it's baseline (e.g. firefox)
- Tags on annotations
- Tkinter GUI over `list_packages`, `annotate` and `sync_all`
