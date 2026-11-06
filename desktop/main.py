from nicegui import context, ui
from desktop import theme
from desktop.tabs import installed, notes, projects


@ui.page('/')
def index():
    context.client.content.classes('p-0')
    ui.colors(primary=theme.system_accent())
    theme.apply_global_css()
    context.client.content.classes('p-0')
    with ui.tabs().props('align=left dense no-caps indicator-color=primary active-color=primary').classes('w-full') as tabs:
        t_inst = ui.tab('Installed')
        t_notes = ui.tab('Notes')
        t_proj = ui.tab('Projects')
    with ui.tab_panels(tabs, value=t_inst).classes('w-full').style('padding: 0'):
        with ui.tab_panel(t_inst):
            installed.build()
        with ui.tab_panel(t_notes):
            notes.build()
        with ui.tab_panel(t_proj):
            projects.build()


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title='Carn', native=True, window_size=(900, 600), reload=False, dark=None)
