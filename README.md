# carn

Track what's installed on your Linux machine, and why. Carn makes it accessible for you to find all installed packages on your computer along with metadata, it's package manager, and it's description.

## Install

```bash
python -m pip install -e .          # CLI only
python -m pip install -e '.[gui]'   # CLI + desktop GUI (NiceGUI)
```

That generates two commands that work from any directory:

| Command | What it does |
|---|---|
| `carn` | Same as `python3 -m carn` (CLI). |
| `carn-gui` | Opens the native desktop window with the Installed / Notes / Projects tabs. |

`carn-gui` needs the `gui` extra (`nicegui`, pinned to 4.0.0). `carn-gui` and `python3 -m desktop.main` start the same app and share the database at `~/.local/share/carn/carn.db`.


## Usage

Run `sync` once first — the db starts empty.

From the project root (or use `carn` from anywhere after installing):

```bash
carn sync                              # scan all package managers into the db
carn list                              # software you installed yourself
carn list --all                        # ...plus base-system packages
carn list --source snap                # one source only (-s)
carn list docker                       # search name, summary, notes and tags
carn note apt docker-ce containers for local dev
```

If you don't have an install, replace `carn` with `python3 -m carn`.

| Command | What it does |
|---|---|
| `sync` | This runs every available scanner and updates the db. It prints one status line per source. |
| `list [search]` | This command shows packages. Default: manual, non-baseline (meaning, manual packages shipped with your OS), still-installed ones. |
| `list -a / --all` | Also includes "baseline" packages. |
| `list -s / --source` | Filters to one source, say, `apt`, `snap`, `flatpak`, `pipx`, `bin`, `appimage`. |
| `note <source> <name> <text>` | You can add notes. It overwrites any earlier note, quotes optional. Also, it would warn if the package hasn't been scanned yet, but it still saves it. |


## How it works

- **Scanners** (`carn/scanners/`) fetch and parse one package manager each into `Package` objects. They know nothing about the db.
- **Core data** (`packages` table) is rewritten on every `sync`. Packages that disappear get a `removed_at` timestamp instead of being deleted.
- **Annotations** (`annotations` table) are your notes. A scan never touches them, so notes survive removing and reinstalling a package.
- **Default view** = `manual = 1` and `baseline` is not 1 (`NULL` still counts as yours); removed packages are hidden.
  - `manual`: you installed it, rather than it arriving as a dependency (apt: `apt-mark showmanual`; snap: a heuristic on snap type and apps).
  - `baseline`: it shipped with the OS (apt: first installed within 24h of the oldest `dpkg.log` event; snap: listed in `/var/lib/snapd/seed/seed.yaml`).
- The baseline is stored at the first non-`NULL` value and never recomputed, because dpkg logs rotate. If a scan can't determine it, a later scan can still fill it in.

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

apt, snap, flatpak, bin, appimage, pipx

## Ideas / later

- Pin a package into the default view even if it's baseline (e.g. firefox)
- Downloads manager, yet to decide what I want concerning that
- Reverse search with cli (relatively easy addition)
- Deleting packages from carn
- Other Linux distro-specific package manager scanners
