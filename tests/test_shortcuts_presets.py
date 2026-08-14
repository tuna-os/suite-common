# Unit tests for suite_common.shortcuts_presets — pure data + config logic,
# no display required.
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from suite_common import shortcuts_presets as sp  # noqa: E402


def test_preset_keys_complete():
    """Every preset must cover the full action set (file/edit/view)."""
    actions = {'app.new', 'app.open', 'app.save', 'app.save_as', 'app.close',
               'app.print', 'app.quit', 'app.undo', 'app.redo',
               'app.preferences', 'app.shortcuts'}
    for key, preset in sp.PRESETS.items():
        assert set(preset.keys()) == actions, f'{key}: {set(preset.keys()) ^ actions}'


def test_presets_share_action_set():
    """All presets must define the same action names (no drift)."""
    base = set(sp.PRESETS[sp.DEFAULT_PRESET].keys())
    for key, preset in sp.PRESETS.items():
        assert set(preset.keys()) == base, key


def test_default_preset_present():
    assert sp.DEFAULT_PRESET in sp.PRESETS
    assert sp.DEFAULT_PRESET == 'google-docs'


def test_accelerator_syntax():
    """Every accelerator must be a non-empty string (modifier chords or
    bare function keys like F12 are both valid GTK accels)."""
    for key, preset in sp.PRESETS.items():
        for action, accels in preset.items():
            assert isinstance(accels, list) and accels, f'{key}/{action}: empty'
            for accel in accels:
                assert isinstance(accel, str) and accel, f'{key}/{action}: bad accel'


def test_accelerators_are_gtk_syntax():
    """Chords must be angle-bracketed modifiers; bare keys must be real
    key names (F12 is the only bare form the presets use)."""
    for key, preset in sp.PRESETS.items():
        for action, accels in preset.items():
            for accel in accels:
                if '<' in accel:
                    assert accel.startswith('<') and '>' in accel, \
                        f'{key}/{action}: malformed chord {accel!r}'
                else:
                    assert accel in ('F12',), \
                        f'{key}/{action}: unexpected bare accel {accel!r}'


def test_save_as_differs_across_presets():
    """Word uses F12 for Save As; the web presets use the shifted chord."""
    assert 'F12' in sp.PRESETS['microsoft-word']['app.save_as']
    assert '<primary><shift>s' in sp.PRESETS['google-docs']['app.save_as']
    assert '<primary><shift>s' in sp.PRESETS['libreoffice']['app.save_as']


def test_macos_uses_meta():
    """The macOS preset must use <meta> (Command) not <primary>."""
    for action, accels in sp.PRESETS['macos'].items():
        for accel in accels:
            assert '<meta>' in accel, f'macos/{action}: {accel!r} uses non-meta modifier'


def test_build_shortcuts_display_default():
    display = sp.build_shortcuts_display()
    assert set(display.keys()) == {'File', 'Edit', 'View'}
    # File section: new/open/save/save_as/close/print/quit in order.
    file_items = [a for a, _ in display['File']]
    assert file_items == ['<primary>n', '<primary>o', '<primary>s',
                          '<primary><shift>s', '<primary>w', '<primary>p',
                          '<primary>q']


def test_build_shortcuts_display_macos():
    display = sp.build_shortcuts_display('macos')
    file_accels = [a for a, _ in display['File']]
    assert file_accels[0] == '<meta>n'
    assert '<meta>q' in file_accels


def test_build_shortcuts_display_word_f12():
    display = sp.build_shortcuts_display('microsoft-word')
    assert 'F12' in [a for a, _ in display['File']]


def test_build_shortcuts_display_unknown_preset_falls_back():
    display = sp.build_shortcuts_display('no-such-preset')
    assert [a for a, _ in display['File']][0] == '<primary>n'


def test_load_preset_default_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(sp, '_CONFIG_BASE', str(tmp_path))
    assert sp.load_preset('org.tunaos.letters') == sp.DEFAULT_PRESET


def test_load_preset_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(sp, '_CONFIG_BASE', str(tmp_path))
    sp.save_preset('org.tunaos.letters', 'microsoft-word')
    assert sp.load_preset('org.tunaos.letters') == 'microsoft-word'


def test_load_preset_ignores_bad_json(tmp_path, monkeypatch):
    monkeypatch.setattr(sp, '_CONFIG_BASE', str(tmp_path))
    app_id = 'org.tunaos.letters'
    path = sp._config_path(app_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        fh.write('{not json')
    assert sp.load_preset(app_id) == sp.DEFAULT_PRESET


def test_load_preset_ignores_unknown_key(tmp_path, monkeypatch):
    monkeypatch.setattr(sp, '_CONFIG_BASE', str(tmp_path))
    app_id = 'org.tunaos.letters'
    path = sp._config_path(app_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        json.dump({'preset': 'vim'}, fh)
    assert sp.load_preset(app_id) == sp.DEFAULT_PRESET


def test_save_preset_creates_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(sp, '_CONFIG_BASE', str(tmp_path))
    sp.save_preset('org.tunaos.letters', 'libreoffice')
    assert sp.load_preset('org.tunaos.letters') == 'libreoffice'
