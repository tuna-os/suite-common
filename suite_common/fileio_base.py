# fileio_base.py — shared file-I/O scaffolding for the suite.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Two pieces:
#  * a format registry (extension -> reader/writer) with dispatch helpers — pure
#    functions, unit-testable without a display (see tests/);
#  * FileDialogController — wraps Gtk.FileDialog open/save so each app only wires
#    callbacks. Tables and Decks register their adapters (csv/xlsx/ods, pptx/odp).

import os

# ----- format registry (pure, testable) ------------------------------------

_READERS = {}
_WRITERS = {}


def register(ext, reader=None, writer=None):
    ext = ext.lower()
    if reader:
        _READERS[ext] = reader
    if writer:
        _WRITERS[ext] = writer


def read(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in _READERS:
        raise ValueError(f'No reader for {ext}')
    return _READERS[ext](path)


def write(path, model):
    ext = os.path.splitext(path)[1].lower()
    if ext not in _WRITERS:
        raise ValueError(f'No writer for {ext}')
    return _WRITERS[ext](path, model)


def patterns():
    exts = sorted(set(_READERS) | set(_WRITERS))
    return ['*' + e for e in exts]


# Reference adapter: a trivial newline-delimited text format ('.txt'), used to
# exercise the registry end-to-end in tests without any heavy dependency.
def _read_txt(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read().splitlines()


def _write_txt(path, model):
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(model))


register('.txt', _read_txt, _write_txt)


# ----- dialog controller (needs GTK; imported lazily) -----------------------

class FileDialogController:
    def __init__(self, window, name='Documents'):
        self._window = window
        self._name = name

    def _filter(self):
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk, Gio
        flt = Gtk.FileFilter()
        flt.set_name(self._name)
        for pat in patterns():
            flt.add_pattern(pat)
        store = Gio.ListStore.new(Gtk.FileFilter)
        store.append(flt)
        return store

    def open(self, on_path):
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk, GLib
        dialog = Gtk.FileDialog(title='Open')
        dialog.set_filters(self._filter())

        def done(dlg, res):
            try:
                gfile = dlg.open_finish(res)
            except GLib.Error:
                return
            on_path(gfile.get_path())
        dialog.open(self._window, None, done)

    def save(self, initial, on_path):
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk, GLib
        dialog = Gtk.FileDialog(title='Save')
        dialog.set_initial_name(initial)

        def done(dlg, res):
            try:
                gfile = dlg.save_finish(res)
            except GLib.Error:
                return
            on_path(gfile.get_path())
        dialog.save(self._window, None, done)
