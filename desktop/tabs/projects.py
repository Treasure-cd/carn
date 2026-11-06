# desktop/tabs/projects.py
import sqlite3

from nicegui import context, ui

from desktop import data
from desktop.components import package_picker

_state = {'selected': None}

COLUMNS = [
    {'name': 'source', 'label': 'Source', 'field': 'source', 'align': 'left', 'sortable': True},
    {'name': 'name', 'label': 'Name', 'field': 'label', 'align': 'left', 'sortable': True},
    {'name': 'summary', 'label': 'Description', 'field': 'summary', 'align': 'left',
     'style': 'max-width: 360px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'},
    {'name': 'actions', 'label': '', 'field': 'actions', 'align': 'right'},
]


def _select(project_id: int) -> None:
    _state['selected'] = project_id
    projects_view.refresh()


def _open_form(project: dict | None = None) -> None:
    """Create a project, or edit/delete an existing one."""
    armed = {'delete': False}

    def save() -> None:
        name = (name_in.value or '').strip()
        if not name:
            ui.notify('Give it a name', type='warning')
            return
        try:
            if project:
                data.update_project(project['id'], name, desc.value or '')
                _state['selected'] = project['id']
            else:
                _state['selected'] = data.create_project(name, desc.value or '')
        except sqlite3.IntegrityError:
            ui.notify('A project with that name already exists', type='negative')
            return
        dlg.close()
        projects_view.refresh()

    def delete(btn) -> None:
        if not armed['delete']:
            armed['delete'] = True
            btn.text = 'Click again to confirm'
            return
        data.delete_project(project['id'])
        _state['selected'] = None
        ui.notify('Project deleted')
        dlg.close()
        projects_view.refresh()

    with context.client.content, ui.dialog() as dlg, ui.card().classes('w-[480px] max-w-full'):
        ui.label('Edit project' if project else 'New project').classes('text-lg font-medium')
        name_in = ui.input('Name', value=project['name'] if project else '').props(
            'outlined dense autofocus').classes('w-full')
        desc = ui.textarea('What is it for?', value=(project or {}).get('description') or '').props(
            'outlined input-style="min-height: 80px"').classes('w-full')
        with ui.row().classes('w-full items-center mt-2'):
            if project:
                del_btn = ui.button('Delete project').props('flat no-caps color=negative')
                del_btn.on_click(lambda: delete(del_btn))
            ui.space()
            ui.button('Cancel', on_click=dlg.close).props('flat no-caps')
            ui.button('Save', on_click=save).props('no-caps')
    dlg.on('hide', lambda: dlg.delete())
    dlg.open()


def _add_packages(project: dict) -> None:
    members = {(r['source'], r['name']) for r in data.project_packages(project['id'])}

    def pick(pkg: dict) -> None:
        data.add_to_project(project['id'], pkg['source'], pkg['name'])
        members.add((pkg['source'], pkg['name']))
        ui.notify(f"Added {pkg['name']}")
        projects_view.refresh()

    package_picker.open_picker(
        f"Add to {project['name']}", pick, keep_open=True,
        mark=lambda r: 'Already in this project' if (r['source'], r['name']) in members else None,
    )


@ui.refreshable
def projects_view() -> None:
    projects = data.projects()
    if _state['selected'] not in {p['id'] for p in projects}:
        _state['selected'] = projects[0]['id'] if projects else None
    current = next((p for p in projects if p['id'] == _state['selected']), None)

    with ui.row().classes('w-full no-wrap gap-0'):
        with ui.column().classes('w-64 shrink-0 gap-0 p-2'):
            ui.button('New project', icon='add', on_click=lambda: _open_form()).props(
                'dense no-caps').classes('w-full mb-2')
            with ui.list().props('dense').classes('w-full'):
                for p in projects:
                    item = ui.item(on_click=lambda p=p: _select(p['id']))
                    if p['id'] == _state['selected']:
                        item.props('active')
                    with item:
                        with ui.item_section():
                            ui.item_label(p['name'])
                            ui.item_label(f"{p['n']} package{'s' if p['n'] != 1 else ''}").props('caption')

        with ui.column().classes('grow min-w-0 p-2'):
            if not current:
                ui.label('No projects yet. Create one to group packages by what they are for.').classes(
                    'text-grey-6 p-4')
                return

            with ui.row().classes('w-full items-center no-wrap'):
                with ui.column().classes('grow gap-0 min-w-0'):
                    ui.label(current['name']).classes('text-lg font-medium')
                    if current['description']:
                        ui.label(current['description']).classes('text-sm text-grey-7')
                ui.button('Edit', icon='edit', on_click=lambda: _open_form(current)).props('flat dense no-caps')
                ui.button('Add package', icon='add', on_click=lambda: _add_packages(current)).props(
                    'dense no-caps')

            rows = data.project_packages(current['id'])
            for r in rows:
                r['id'] = f"{r['source']}/{r['name']}"
                r['label'] = r['name'] + (' (removed)' if r['removed_at'] else '')
                r['summary'] = r['summary'] or ''
            tbl = ui.table(
                columns=COLUMNS, rows=rows, row_key='id', pagination={'rowsPerPage': 0},
            ).props('flat dense virtual-scroll no-data-label="Empty. Click Add package."')
            tbl.classes('w-full').style('height: calc(100vh - 190px)')
            tbl.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn flat dense round size="sm" icon="close"
                           @click.stop="$parent.$emit('remove', props.row)" />
                </q-td>
            ''')
            tbl.on('remove', lambda e: (
                data.remove_from_project(current['id'], e.args['source'], e.args['name']),
                projects_view.refresh(),
            ))


def build() -> None:
    projects_view()
