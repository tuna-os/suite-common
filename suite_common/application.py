# application.py — shared Adw.Application base for the suite.
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw  # noqa: E402

from . import shortcuts_presets  # noqa: E402

# _() for translations.  The launcher script (tables.in / decks.in) sets
# the text domain; this import provides a fallback during development.
try:
    from gettext import gettext as _
except ImportError:
    def _(s):
        return s


def _setup_dark_mode(on_change=None):
    """Apply system dark mode preference to WebKit webviews.

    Args:
        on_change: Optional callback(is_dark) called when the
                   preference changes.  Apps pass a function that
                   sends the preference to their JS engine.

    Returns:
        bool: initial dark mode state.
    """
    style_mgr = Adw.StyleManager.get_default()
    dark = style_mgr.get_dark()

    def _on_dark_changed(mgr):
        if on_change:
            on_change(mgr.get_dark())

    if on_change:
        style_mgr.connect('notify::dark', _on_dark_changed)
    return dark


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

        # Load the saved shortcut preset (or the Google Docs default).
        self._shortcut_preset = shortcuts_presets.load_preset(application_id)

        # Build the initial shortcuts display dict from preset defaults.
        self.shortcuts = shortcuts_presets.build_shortcuts_display(
            self._shortcut_preset)

        # ── Register all actions (accelerators come from the preset) ──
        preset_accels = shortcuts_presets.PRESETS[self._shortcut_preset]

        # ── File ────────────────────────────────────────────────────
        self._add_action('new', self._on_new,
                         preset_accels.get('app.new', ['<primary>n']))
        self._add_action('open', self._on_open,
                         preset_accels.get('app.open', ['<primary>o']))
        self._add_action('save', self._on_save,
                         preset_accels.get('app.save', ['<primary>s']))
        self._add_action('save_as', self._on_save_as,
                         preset_accels.get('app.save_as', ['<primary><shift>s']))
        self._add_action('close', self._on_close,
                         preset_accels.get('app.close', ['<primary>w']))
        self._add_action('print', self._on_print,
                         preset_accels.get('app.print', ['<primary>p']))

        # ── Edit ────────────────────────────────────────────────────
        self._add_action('undo', self._on_undo,
                         preset_accels.get('app.undo', ['<primary>z']))
        self._add_action('redo', self._on_redo,
                         preset_accels.get('app.redo',
                                           ['<primary><shift>z', '<primary>y']))

        # ── App ─────────────────────────────────────────────────────
        self._add_action('quit', lambda *a: self.quit(),
                         preset_accels.get('app.quit', ['<primary>q']))
        self._add_action('about', self._on_about)
        self._add_action('preferences', self._on_preferences,
                         preset_accels.get('app.preferences', ['<primary>comma']))
        self._add_action('shortcuts', self._on_shortcuts,
                         preset_accels.get('app.shortcuts', ['<primary>question']))

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
        # Rebuild shortcuts display from the current preset so the
        # overlay always shows the active accelerators.
        self.shortcuts = shortcuts_presets.build_shortcuts_display(
            self._shortcut_preset)
        win = build_shortcuts_dialog(self.shortcuts)
        win.set_transient_for(self.props.active_window)
        win.present()

    # ── Shortcut preset ──────────────────────────────────────────

    def get_shortcut_preset(self):
        """Return the current shortcut preset key."""
        return self._shortcut_preset

    def set_shortcut_preset(self, preset_key):
        """Switch to *preset_key* and persist the choice.

        Updates all Gio.Action accelerators and the shortcuts overlay
        display dictionary.
        """
        if preset_key not in shortcuts_presets.PRESETS:
            return
        self._shortcut_preset = preset_key
        accels = shortcuts_presets.PRESETS[preset_key]
        for action_name, accel_list in accels.items():
            self.set_accels_for_action(action_name, accel_list)
        self.shortcuts = shortcuts_presets.build_shortcuts_display(preset_key)
        shortcuts_presets.save_preset(self.get_application_id(), preset_key)

    def _on_about(self, *args):
        about = Adw.AboutDialog(
            application_name=self.app_name,
            application_icon=self.get_application_id(),
            version=self.version,
            developer_name='hanthor',
            license_type=Gtk.License.GPL_3_0,
        )
        about.present(self.props.active_window)
