# application.py — shared Adw.Application base for the suite.
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw  # noqa: E402


class SuiteApplication(Adw.Application):
    """Base application: window lifecycle + quit/about actions.

    Apps subclass this and pass their window class + display name. This is the
    extraction point for what Letters does in its own ``main.py`` so Tables,
    Decks, and Letters share one shell. See SPEC.md.
    """

    def __init__(self, application_id, window_class, app_name, version='0.1.0'):
        super().__init__(application_id=application_id,
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self._window_class = window_class
        self.app_name = app_name
        self.version = version

        # Apps may override/extend this before/after super().__init__.
        self.shortcuts = {
            'General': [
                ('<primary>o', 'Open'),
                ('<primary>s', 'Save'),
                ('<primary>comma', 'Preferences'),
                ('<primary>q', 'Quit'),
            ],
        }

        self._add_action('quit', lambda *a: self.quit(), ['<primary>q'])
        self._add_action('about', self._on_about)
        self._add_action('preferences', self._on_preferences, ['<primary>comma'])
        self._add_action('shortcuts', self._on_shortcuts, ['<primary>question'])

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = self._window_class(application=self)
        win.present()

    def do_open(self, files, n_files, hint):
        # Minimal: just present the window for now. File handling lands in the
        # file-I/O base class slice (suite-common #4).
        self.activate()

    def _add_action(self, name, callback, accels=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        if accels:
            self.set_accels_for_action(f'app.{name}', accels)

    def _on_preferences(self, *args):
        from .dialogs import SuitePreferencesDialog
        SuitePreferencesDialog(self.app_name).present(self.props.active_window)

    def _on_shortcuts(self, *args):
        from .dialogs import build_shortcuts_dialog
        win = build_shortcuts_dialog(self.shortcuts)
        win.set_transient_for(self.props.active_window)
        win.present()

    def _on_about(self, *args):
        about = Adw.AboutDialog(
            application_name=self.app_name,
            application_icon=self.get_application_id(),
            version=self.version,
            developer_name='hanthor',
            license_type=Gtk.License.GPL_3_0,
        )
        about.present(self.props.active_window)
