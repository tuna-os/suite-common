# dialogs.py — shared preferences + keyboard-shortcuts chrome for the suite.
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw  # noqa: E402


class SuitePreferencesDialog(Adw.PreferencesDialog):
    """A minimal preferences scaffold. Apps add their own groups/rows."""

    def __init__(self, app_name='App'):
        super().__init__()
        self.set_title('Preferences')
        page = Adw.PreferencesPage(title='General',
                                   icon_name='preferences-system-symbolic')
        self.general_group = Adw.PreferencesGroup(title='Appearance')

        # A real, working preference: force dark style via the style manager.
        manager = Adw.StyleManager.get_default()
        dark_row = Adw.SwitchRow(title='Dark Style',
                                 subtitle='Always use the dark colour scheme')
        dark_row.set_active(manager.get_dark())
        dark_row.connect('notify::active', self._on_dark_toggled)
        self.general_group.add(dark_row)

        page.add(self.general_group)
        self.add(page)

    def _on_dark_toggled(self, row, _param):
        manager = Adw.StyleManager.get_default()
        manager.set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if row.get_active() else Adw.ColorScheme.DEFAULT)


def build_shortcuts_dialog(groups):
    """Build a Gtk.ShortcutsWindow from {section: [(accel, label), ...]}.

    Returns a window the app presents (transient to the active window).
    """
    section = Gtk.ShortcutsSection(visible=True, max_height=10)
    for title, shortcuts in groups.items():
        group = Gtk.ShortcutsGroup(title=title, visible=True)
        for accel, label in shortcuts:
            group.add_shortcut(Gtk.ShortcutsShortcut(
                visible=True, accelerator=accel, title=label))
        section.add_group(group)
    window = Gtk.ShortcutsWindow(modal=True)
    window.add_section(section)
    return window
