# Unit tests for suite_common.fileio_base — pure, no display required.
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from suite_common import fileio_base as fio  # noqa: E402


def test_reference_txt_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'doc.txt')
        model = ['alpha', 'beta', 'gamma']
        fio.write(path, model)
        assert fio.read(path) == model


def test_registry_dispatch_and_patterns():
    assert '*.txt' in fio.patterns()
    fio.register('.rev',
                 reader=lambda p: open(p, encoding='utf-8').read()[::-1],
                 writer=lambda p, m: open(p, 'w', encoding='utf-8').write(m[::-1]))
    assert '*.rev' in fio.patterns()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'x.rev')
        fio.write(path, 'hello')
        assert fio.read(path) == 'hello'


def test_unknown_extension_raises():
    try:
        fio.read('/tmp/nope.unknownext')
    except ValueError:
        pass
    else:
        raise AssertionError('expected ValueError for unknown reader extension')

    try:
        fio.write('/tmp/nope.unknownext', 'data')
    except ValueError:
        pass
    else:
        raise AssertionError('expected ValueError for unknown writer extension')


def test_write_unknown_extension_raises():
    try:
        fio.write('/tmp/nope.unknownext', [])
    except ValueError:
        return
    raise AssertionError('expected ValueError for unknown extension')


def test_file_dialog_controller():
    class DummyFilter:
        def __init__(self):
            self.name = None
            self.patterns = []

        def set_name(self, name):
            self.name = name

        def add_pattern(self, pat):
            self.patterns.append(pat)

    class DummyListStore:
        def __init__(self):
            self.items = []

        @classmethod
        def new(cls, _type):
            return cls()

        def append(self, item):
            self.items.append(item)

    class DummyGFile:
        def __init__(self, path):
            self._path = path

        def get_path(self):
            return self._path

    class DummyFileDialog:
        def __init__(self, title):
            self.title = title
            self.filters = None
            self.initial_name = None

        def set_filters(self, store):
            self.filters = store

        def set_initial_name(self, name):
            self.initial_name = name

        def open(self, window, cancellable, callback):
            res = object()
            callback(self, res)

        def open_finish(self, res):
            return DummyGFile('/tmp/opened.txt')

        def save(self, window, cancellable, callback):
            res = object()
            callback(self, res)

        def save_finish(self, res):
            return DummyGFile('/tmp/saved.txt')

    class DummyGiRepository:
        Gtk = type('Gtk', (), {
            'FileFilter': DummyFilter,
            'ListStore': DummyListStore,
            'FileDialog': DummyFileDialog,
        })
        Gio = type('Gio', (), {'ListStore': DummyListStore})
        GLib = type('GLib', (), {'Error': Exception})

    class DummyGi:
        @staticmethod
        def require_version(name, version):
            pass

        repository = DummyGiRepository

    import sys
    orig_gi = sys.modules.get('gi')
    orig_gi_repo = sys.modules.get('gi.repository')
    sys.modules['gi'] = DummyGi
    sys.modules['gi.repository'] = DummyGiRepository
    try:
        ctrl = fio.FileDialogController(window=None, name='TestDocs')
        opened_path = []
        ctrl.open(on_path=lambda p: opened_path.append(p))
        assert opened_path == ['/tmp/opened.txt']

        saved_path = []
        ctrl.save('doc.txt', on_path=lambda p: saved_path.append(p))
        assert saved_path == ['/tmp/saved.txt']
    finally:
        if orig_gi is not None:
            sys.modules['gi'] = orig_gi
        else:
            sys.modules.pop('gi', None)
        if orig_gi_repo is not None:
            sys.modules['gi.repository'] = orig_gi_repo
        else:
            sys.modules.pop('gi.repository', None)


if __name__ == '__main__':
    test_reference_txt_roundtrip()
    test_registry_dispatch_and_patterns()
    test_unknown_extension_raises()
    test_write_unknown_extension_raises()
    test_file_dialog_controller()
    print('fileio_base tests: PASS')


