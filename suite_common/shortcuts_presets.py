# shortcuts_presets.py — keyboard shortcut preset profiles.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Defines preset profiles that map action names to GTK accelerator strings.
# Apps consume this to let users switch between Google Docs, Word, macOS,
# and LibreOffice keyboard shortcut conventions.
#
# Each preset is a dict keyed by action name (the same names passed to
# Gio.Application.set_accels_for_action) and holds a list of accelerator
# strings.  When a preset is applied only the accelerators listed here are
# changed; any action not listed keeps its app-defined default.

try:
    from gettext import gettext as _
except ImportError:
    def _(s):
        return s

# ── Preset display metadata ───────────────────────────────────────────

PRESET_LABELS = {
    'google-docs':    _('Google Docs'),
    'microsoft-word': _('Microsoft Word'),
    'macos':          _('macOS'),
    'libreoffice':    _('LibreOffice'),
}

DEFAULT_PRESET = 'google-docs'

# ── Preset accelerator maps (action name → list of accel strings) ─────

PRESETS = {
    'google-docs': {
        # ── File ──
        'app.new':         ['<primary>n'],
        'app.open':        ['<primary>o'],
        'app.save':        ['<primary>s'],
        'app.save_as':     ['<primary><shift>s'],
        'app.close':       ['<primary>w'],
        'app.print':       ['<primary>p'],
        'app.quit':        ['<primary>q'],
        # ── Edit ──
        'app.undo':        ['<primary>z'],
        'app.redo':        ['<primary><shift>z', '<primary>y'],
        # ── View ──
        'app.preferences': ['<primary>comma'],
        'app.shortcuts':   ['<primary>question'],
    },

    'microsoft-word': {
        # ── File ──
        'app.new':         ['<primary>n'],
        'app.open':        ['<primary>o'],
        'app.save':        ['<primary>s'],
        'app.save_as':     ['F12'],
        'app.close':       ['<primary>w'],
        'app.print':       ['<primary>p'],
        'app.quit':        ['<alt>F4'],
        # ── Edit ──
        'app.undo':        ['<primary>z'],
        'app.redo':        ['<primary>y'],
        # ── View ──
        'app.preferences': ['<primary>comma'],
        'app.shortcuts':   ['<primary>question'],
    },

    'macos': {
        # ── File ──
        'app.new':         ['<meta>n'],
        'app.open':        ['<meta>o'],
        'app.save':        ['<meta>s'],
        'app.save_as':     ['<meta><shift>s'],
        'app.close':       ['<meta>w'],
        'app.print':       ['<meta>p'],
        'app.quit':        ['<meta>q'],
        # ── Edit ──
        'app.undo':        ['<meta>z'],
        'app.redo':        ['<meta><shift>z'],
        # ── View ──
        'app.preferences': ['<meta>comma'],
        'app.shortcuts':   ['<meta>question'],
    },

    'libreoffice': {
        # ── File ──
        'app.new':         ['<primary>n'],
        'app.open':        ['<primary>o'],
        'app.save':        ['<primary>s'],
        'app.save_as':     ['<primary><shift>s'],
        'app.close':       ['<primary>w'],
        'app.print':       ['<primary>p'],
        'app.quit':        ['<primary>q'],
        # ── Edit ──
        'app.undo':        ['<primary>z'],
        'app.redo':        ['<primary><shift>z', '<primary>y'],
        # ── View ──
        'app.preferences': ['<primary>comma'],
        'app.shortcuts':   ['<primary>question'],
    },
}


# ── Shortcuts overlay labels (displayed in Ctrl+? dialog) ─────────────
# These mirror SuiteApplication.shortcuts so the overlay stays in sync
# when a profile is applied.


def build_shortcuts_display(preset_key=None):
    """Return a {section: [(accel, label), ...]} dict for the shortcuts overlay.

    When *preset_key* is provided the accelerators are drawn from that preset;
    otherwise the Google Docs defaults are used.
    """
    preset = PRESETS.get(preset_key, PRESETS[DEFAULT_PRESET])

    # Map each action back to its display label.  Keep in the same order
    # as the original SuiteApplication.shortcuts.
    action_labels = {
        'app.new':         _('New'),
        'app.open':        _('Open'),
        'app.save':        _('Save'),
        'app.save_as':     _('Save As'),
        'app.close':       _('Close'),
        'app.print':       _('Print / Export'),
        'app.quit':        _('Quit'),
        'app.undo':        _('Undo'),
        'app.redo':        _('Redo'),
        'app.preferences': _('Preferences'),
        'app.shortcuts':   _('Keyboard Shortcuts'),
    }

    file_order = ['app.new', 'app.open', 'app.save', 'app.save_as',
                  'app.close', 'app.print', 'app.quit']
    edit_order = ['app.undo', 'app.redo']
    view_order = ['app.preferences', 'app.shortcuts']

    result = {}
    for section_title, order in [
        (_('File'), file_order),
        (_('Edit'), edit_order),
        (_('View'), view_order),
    ]:
        items = []
        for action in order:
            accels = preset.get(action, [])
            label = action_labels.get(action, action)
            for accel in accels:
                items.append((accel, label))
        result[section_title] = items
    return result


# ── Config persistence ─────────────────────────────────────────────────

import os
import json

try:
    from gi.repository import GLib
    _CONFIG_BASE = os.path.join(GLib.get_user_config_dir(), 'tuna-suite')
except (ImportError, AttributeError):
    _CONFIG_BASE = os.path.join(os.path.expanduser('~/.config'), 'tuna-suite')


def _config_path(app_id):
    """Return the path to the shortcut-preset config file for *app_id*."""
    return os.path.join(_CONFIG_BASE, app_id, 'shortcut-preset.json')


def load_preset(app_id):
    """Return the saved preset key for *app_id*, or DEFAULT_PRESET."""
    path = _config_path(app_id)
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        key = data.get('preset', DEFAULT_PRESET)
        if key in PRESETS:
            return key
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return DEFAULT_PRESET


def save_preset(app_id, preset_key):
    """Persist *preset_key* for *app_id*."""
    path = _config_path(app_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump({'preset': preset_key}, fh)
