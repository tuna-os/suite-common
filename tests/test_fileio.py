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
        return
    raise AssertionError('expected ValueError for unknown extension')


if __name__ == '__main__':
    test_reference_txt_roundtrip()
    test_registry_dispatch_and_patterns()
    test_unknown_extension_raises()
    print('fileio_base tests: PASS')
