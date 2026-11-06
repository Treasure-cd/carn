from nicegui import context, ui

from desktop import data
from desktop.components import package_picker
from desktop.tabs import installed

_state = {'search': ''}

_ELLIPSIS = 'max-width: 420px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'
COLUMNS = [
    {'name': 'source', 'label': 'Source', 'field': 'source', 'align': 'left', 'sortable': True},
    {'name': 'name', 'label': 'Name', 'field': 'label', 'align': 'left', 'sortable': True},
    {'name': 'note', 'label': 'Note', 'field': 'note', 'align': 'left',
     'style': _ELLIPSIS, 'headerStyle': _ELLIPSIS},
    {'name': 'updated', 'label': 'Edited', 'field': 'updated', 'align': 'left', 'sortable': True},
]


def _changed() -> None:
    """A note was saved or deleted: refresh both tabs."""
    notes_table.refresh()
    installed.refresh()


def _open_editor(pkg: dict) -> None:
    """The only place notes are written. pkg needs source, name; summary/note/removed_at optional."""
    existing = bool(pkg.get('note'))

    def save() -> None:
        data.save_note(pkg['source'], pkg['name'], area.value)
        ui.notify('Note saved' if area.value.strip() else 'Note cleared')
        dlg.close()
        _changed()

    def delete() -> None:
        data.delete_note(pkg['source'], pkg['name'])
        ui.notify('Note deleted')
        dlg.close()
        _changed()

    with context.client.content, ui.dialog() as dlg, ui.card().classes('w-[520px] max-w-full'):
        ui.label(pkg['name']).classes('text-lg font-medium')
        sub = f"{pkg['source']}" + (f" · {pkg['summary']}" if pkg.get('summary') else '')
        ui.label(sub).classes('text-sm text-grey-7')
        if pkg.get('removed_at'):
            ui.label('No longer installed').classes('text-xs text-orange-8')
        area = ui.textarea(
            label='Why do you have this?', value=pkg.get('note') or '',
        ).props('outlined autofocus input-style="min-height: 120px"').classes('w-full mt-2')
        with ui.row().classes('w-full items-center mt-2'):
            if existing:
                ui.button('Delete', on_click=delete).props('flat no-caps color=negative')
            ui.space()
            ui.button('Cancel', on_click=dlg.close).props('flat no-caps')
            ui.button('Save', on_click=save).props('no-caps')
    dlg.on('hide', lambda: dlg.delete())
    dlg.open()


def _open_picker() -> None:
    package_picker.open_picker(
        'Add a note', _open_editor,
        mark=lambda r: 'Already has a note' if r['note'] else None,
    )


@ui.refreshable
def notes_table() -> None:
    rows = data.notes(search=_state['search'])
    for r in rows:
        r['id'] = f"{r['source']}/{r['name']}"
        r['label'] = r['name'] + (' (removed)' if r['removed_at'] else '')
        r['updated'] = (r['updated_at'] or '')[:10]
    by_id = {r['id']: r for r in rows}

    ui.label(f'{len(rows)} notes').classes('text-xs text-grey-6 px-3 pb-1')
    tbl = ui.table(
        columns=COLUMNS, rows=rows, row_key='id',
        pagination={'rowsPerPage': 0},
    ).props('flat dense virtual-scroll no-data-label="No notes yet. Click Add note."')
    tbl.classes('w-full cursor-pointer').style('height: calc(100vh - 130px)')
    tbl.on('rowClick', lambda e: _open_editor(by_id[e.args[1]['id']]))


def _search(value: str) -> None:
    _state['search'] = value or ''
    notes_table.refresh()


def build() -> None:
    with ui.row().classes('w-full items-center gap-2 p-2 no-wrap'):
        ui.input(
            placeholder='Search notes',
            on_change=lambda e: _search(e.value),
        ).props('dense outlined clearable debounce=250').classes('grow')
        ui.button('Add note', icon='add', on_click=_open_picker).props('dense no-caps')
    notes_table()
