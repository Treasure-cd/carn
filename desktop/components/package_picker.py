from collections.abc import Callable

from nicegui import context, ui

from desktop import data


def open_picker(
    title: str,
    on_pick: Callable[[dict], None],
    *,
    mark: Callable[[dict], str | None] | None = None,
    keep_open: bool = False,
) -> None:
    # keep_open leaves the dialog up so several packages can be picked in a row
    def pick(pkg: dict) -> None:
        if keep_open:
            on_pick(pkg)
            search()
        else:
            dlg.close()
            on_pick(pkg)

    def search() -> None:
        results.clear()
        rows = data.find_packages(box.value or '')
        with results:
            if not rows:
                ui.label('No matching packages').classes('text-sm text-grey-6 p-2')
            for r in rows[:50]:
                with ui.item(on_click=lambda r=r: pick(r)).classes('w-full'):
                    with ui.item_section():
                        ui.item_label(r['name'])
                        caption = r['source'] + (f" · {r['summary']}" if r['summary'] else '')
                        ui.item_label(caption).props('caption lines=1')
                    tip = mark(r) if mark else None
                    if tip:
                        with ui.item_section().props('side'):
                            ui.icon('check_circle', size='xs').tooltip(tip)
            if len(rows) > 50:
                ui.label('Carn is showing the first 50 it can grab, help it by searching to narrow down.').classes('text-xs text-grey-6 p-2')

    with context.client.content, ui.dialog() as dlg, ui.card().classes('w-[520px] max-w-full'):
        ui.label(title).classes('text-lg font-medium')
        box = ui.input(placeholder='Search packages').props(
            'dense outlined autofocus clearable debounce=200'
        ).classes('w-full')
        results = ui.list().props('dense separator').classes('w-full').style(
            'max-height: 320px; overflow-y: auto'
        )
        box.on_value_change(lambda _: search())
        with ui.row().classes('w-full justify-end'):
            ui.button('Done' if keep_open else 'Cancel', on_click=dlg.close).props('flat no-caps')
    search()
    dlg.on('hide', lambda: dlg.delete())
    dlg.open()
