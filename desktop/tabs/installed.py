from nicegui import ui
from desktop import data

_state = {'search': '', 'source': '', 'show_all': False}

_ELLIPSIS = 'max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'
COLUMNS = [
    {'name': 'source', 'label': 'Source', 'field': 'source', 'align': 'left', 'sortable': True},
    {'name': 'name', 'label': 'Name', 'field': 'name', 'align': 'left', 'sortable': True},
    {'name': 'summary', 'label': 'Description', 'field': 'summary', 'align': 'left',
     'style': _ELLIPSIS, 'headerStyle': _ELLIPSIS},
    {'name': 'note', 'label': 'Note', 'field': 'note', 'align': 'left', 'sortable': True,
     'style': _ELLIPSIS, 'headerStyle': _ELLIPSIS},
]


def _size(kb) -> str:
    if not kb:
        return 'unknown'
    return f'{kb / 1024:.1f} MB' if kb >= 1024 else f'{kb} KB'


def _field(label: str, value: str, wrap: bool = False):
    ui.label(label).classes('text-xs uppercase text-grey-6 mt-3')
    ui.label(value).classes('text-sm' + (' whitespace-pre-wrap' if wrap else ''))


def _open_detail(row: dict) -> None:
    """Read-only. Notes are edited in the Notes tab."""
    with ui.dialog() as dlg, ui.card().classes('w-[480px] max-w-full'):
        ui.label(row['name']).classes('text-lg font-medium')
        ui.label(f"{row['source']} · {row.get('version') or 'unknown version'}").classes('text-sm text-grey-7')
        _field('Description', row.get('summary') or 'No description')
        if row.get('homepage'):
            _field('Homepage', row['homepage'])
        _field('Size', _size(row.get('size_kb')))
        if row.get('section'):
            _field('Section', row['section'])
        _field('Installed', row.get('install_date') or 'unknown')
        cmd = data.install_cmd(row['source'], row['name'])
        if cmd:
            ui.label('Install command').classes('text-xs uppercase text-grey-6 mt-3')
            with ui.row().classes('w-full items-center no-wrap'):
                ui.label(cmd).classes('text-sm font-mono grow break-all')
                ui.button(
                    icon='content_copy',
                    on_click=lambda: (ui.clipboard.write(cmd), ui.notify('Copied')),
                ).props('flat dense round size=sm')
        _field('First seen', (row.get('first_seen') or '')[:10] or 'unknown')
        projs = data.projects_of(row['source'], row['name'])
        _field('In projects', ', '.join(projs) if projs else 'None')
        _field('Your note', row.get('note') or 'No note yet. Add one in the Notes tab.', wrap=True)
        with ui.row().classes('w-full justify-end mt-4'):
            ui.button('Close', on_click=dlg.close).props('flat no-caps')
    dlg.on('hide', lambda: dlg.delete())
    dlg.open()


@ui.refreshable
def package_table():
    rows = data.installed(
        search=_state['search'], source=_state['source'], show_all=_state['show_all']
    )
    for r in rows:
        r['id'] = f"{r['source']}/{r['name']}"
        r['note'] = r['note'] or ''
        r['summary'] = r['summary'] or ''
    by_id = {r['id']: r for r in rows}

    ui.label(f'{len(rows)} packages').classes('text-xs text-grey-6 px-3 pb-1')
    tbl = ui.table(
        columns=COLUMNS, rows=rows, row_key='id',
        pagination={'rowsPerPage': 0},
    ).props('flat dense virtual-scroll no-data-label="Nothing found. Try Sync."')
    tbl.classes('w-full cursor-pointer').style('height: calc(100vh - 130px)')
    tbl.on('rowClick', lambda e: _open_detail(by_id[e.args[1]['id']]))


# so other tabs can refresh this one after a note changes
refresh = package_table.refresh


def _set(**kw) -> None:
    _state.update(kw)
    package_table.refresh()


async def _sync(btn) -> None:
    btn.props('loading')
    try:
        results = await data.sync()
    except Exception as e:
        ui.notify(f'Sync failed: {e}', type='negative')
    else:
        ui.notify(' · '.join(f'{s}: {st}' for s, st in results.items()))
        package_table.refresh()
    finally:
        btn.props(remove='loading')


def build() -> None:
    with ui.row().classes('w-full items-center gap-2 p-2 no-wrap'):
        ui.input(
            placeholder='Search name, description or note',
            on_change=lambda e: _set(search=e.value or ''),
        ).props('dense outlined clearable debounce=250').classes('grow')
        ui.select(
            {'': 'All sources', **{s: s for s in data.SOURCES}},
            value=_state['source'],
            on_change=lambda e: _set(source=e.value),
        ).props('dense outlined').classes('w-36')
        ui.switch('Base system', on_change=lambda e: _set(show_all=e.value))
        btn = ui.button('Sync', icon='sync').props('dense no-caps')
        btn.on_click(lambda: _sync(btn))
    package_table()
