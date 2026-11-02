- Installed software (core): lists out packages installed on your computer. Sources would be apt, pipx, snap, flatpak, ./local/bin and appimages. apt's switch would be fedora, etc, but we just have to add files ofr stable configuration on non Ububtu/Debian distros. We fetch all of these and parse it into a we;; readable list, which in turn goes into the sqlite database i'll set up.

$ carn scan          # this runs the scanners and updates the database
$ carn list          # list of everything carn knows about, 
$ carn list --source pipx # specific sources 

GUI, there's a table, and you can filter by source.

    - Write one scanner (apt first, I guess) that returns a list of items
    - Write db.py to save and read them
    - Write carn scan and carn list in the CLI.
    - Build the GUI last, once the core works.

carn scan would be run either manually, or on every open of the desktop app. there's an on conflict sql key we can use to see if a package exists in the database already.

- Annotations, extra things you wouldn't usually get from regular details. So like, notes of why they exist. Columns would be: what it does, why I installed it, tags, status (keep, review, remove). consider adding a button to apt uninstall via gui.

Generally, we're doing this
items
  auto fields:  name, version, source, description, section, install_date, install_cmd
  your fields:  why, notes, status, (tags in their own table)


- Projects tab:
Projects are an easier way to store stuff. Several packages can be listed under a project, and it's an easier way to keep track of what was for what.

- Downloads scanner: A more general downloads keeper. Think software-ish downloads and anything else. Compatibility with Chromium and Gecko.

Additional feature:
Reverse search, we can lookfor packages we have based on keywords.
Description of each package from somewhere like tldr pages.

GUI is done in ZeroGUI.
