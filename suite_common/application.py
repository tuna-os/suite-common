# application.py — shared Adw.Application base for the suite.
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw  # noqa: E402

# _() for translations.  The launcher script (tables.in / decks.in) sets
# the text domain; this import provides a fallback during development.
try:
    from gettext import gettext as _
except ImportError:
    def _(s):
        return s


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

        # Keyboard shortcuts shown in the Ctrl+? overlay.
        # Marked for translation with _().  Apps may extend after super().__init__().
        self.shortcuts = {
            _('File'): [
                ('<primary>n', _('New')),
                ('<primary>o', _('Open')),
                ('<primary>s', _('Save')),
                ('<primary><shift>s', _('Save As')),
                ('<primary>w', _('Close')),
                ('<primary>p', _('Print / Export')),
                ('<primary>q', _('Quit')),
            ],
            _('Edit'): [
                ('<primary>z', _('Undo')),
                ('<primary><shift>z', _('Redo')),
            ],
            _('View'): [
                ('<primary>comma', _('Preferences')),
                ('<primary>question', _('Keyboard Shortcuts')),
            ],
        }

        # ── File ────────────────────────────────────────────────────
        self._add_action('new', self._on_new, ['<primary>n'])
        self._add_action('open', self._on_open, ['<primary>o'])
        self._add_action('save', self._on_save, ['<primary>s'])
        self._add_action('save_as', self._on_save_as, ['<primary><shift>s'])
        self._add_action('close', self._on_close, ['<primary>w'])
        self._add_action('print', self._on_print, ['<primary>p'])

        # ── Edit ────────────────────────────────────────────────────
        self._add_action('undo', self._on_undo, ['<primary>z'])
        self._add_action('redo', self._on_redo, ['<primary><shift>z', '<primary>y'])

        # ── App ─────────────────────────────────────────────────────
        self._add_action('quit', lambda *a: self.quit(), ['<primary>q'])
        self._add_action('about', self._on_about)
        self._add_action('preferences', self._on_preferences, ['<primary>comma'])
        self._add_action('shortcuts', self._on_shortcuts, ['<primary>question'])

    # ── Window dispatch ──────────────────────────────────────────────

    def _win(self):
        """Return the active window, or None."""
        return self.props.active_window

    def _call_win(self, method, *args):
        """Call a method on the active window if it exists."""
        win = self._win()
        if win and hasattr(win, method):
            getattr(win, method)(*args)

    # ── File actions ────────────────────────────────────────────────

    def _on_new(self, *a):
        self.activate()  # Opens a new window

    def _on_open(self, *a):
        self._call_win('open_file')

    def _on_save(self, *a):
        self._call_win('save_file')

    def _on_save_as(self, *a):
        self._call_win('save_file_as')

    def _on_close(self, *a):
        win = self._win()
        if win and hasattr(win, 'close'):
            win.close()
        elif win:
            win.close()

    def _on_print(self, *a):
        self._call_win('export_pdf')

    # ── Edit actions ────────────────────────────────────────────────

    def _on_undo(self, *a):
        self._call_win('webview_send', 'undo')

    def _on_redo(self, *a):
        self._call_win('webview_send', 'redo')

    # ── Lifecycle ───────────────────────────────────────────────────

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = self._window_class(application=self)
        win.present()

    def do_open(self, files, n_files, hint):
        self.activate()

    # ── Helpers ─────────────────────────────────────────────────────

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
