from nicegui import ui


def system_accent(fallback='#a05ab4') -> str:
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        found, c = Gtk.Window().get_style_context().lookup_color('theme_selected_bg_color')
        if found:
            return '#%02x%02x%02x' % (round(c.red * 255), round(c.green * 255), round(c.blue * 255))
    except Exception:
        pass
    return fallback


def apply_global_css():
    ui.add_css('''
        .q-tab { min-height: 32px; padding: 0 12px; }
        .q-tab__content { padding: 0; }
        .q-tabs { min-height: 32px; }
    ''')
