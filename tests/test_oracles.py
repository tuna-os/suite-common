# Unit tests for suite_common.oracles — the LibreOffice/openxml-audit test
# oracle helpers. All subprocess/import side effects are mocked; no soffice
# or network needed.
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from suite_common import oracles  # noqa: E402


# ── _soffice availability ────────────────────────────────────────────────

def test_soffice_found(monkeypatch):
    monkeypatch.setattr(oracles, '_SOFFICE', '/usr/bin/soffice')
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        assert oracles._soffice() == '/usr/bin/soffice'


def test_soffice_missing(monkeypatch):
    monkeypatch.setattr(oracles, '_SOFFICE', '/nonexistent/soffice')
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError
        assert oracles._soffice() is None


def test_soffice_version_failure(monkeypatch):
    monkeypatch.setattr(oracles, '_SOFFICE', 'soffice')
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = TimeoutError
        assert oracles._soffice() is None


# ── soffice_to_csv ───────────────────────────────────────────────────────

def test_soffice_to_csv_missing_soffice(monkeypatch):
    monkeypatch.setattr(oracles, '_soffice', lambda: None)
    try:
        oracles.soffice_to_csv('/tmp/x.xlsx')
        assert False, 'expected RuntimeError'
    except RuntimeError as e:
        assert 'soffice not found' in str(e)


def test_soffice_to_csv_success(monkeypatch, tmp_path):
    monkeypatch.setattr(oracles, '_soffice', lambda: '/usr/bin/soffice')
    src = tmp_path / 'book.xlsx'
    src.write_bytes(b'x')

    def fake_run(args, **kwargs):
        # args: [soffice, --headless, --convert-to, csv, --outdir, <td>, in]
        out_dir = args[args.index('--outdir') + 1]
        with open(os.path.join(out_dir, 'book.csv'), 'w') as fh:
            fh.write('a,b\n1,2\n')
        return type('R', (), {'returncode': 0, 'stderr': ''})()

    with patch('subprocess.run', side_effect=fake_run):
        path, text = oracles.soffice_to_csv(str(src))
    assert path.endswith('book.csv')
    assert '1,2' in text


def test_soffice_to_csv_conversion_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(oracles, '_soffice', lambda: '/usr/bin/soffice')
    src = tmp_path / 'book.xlsx'
    src.write_bytes(b'x')

    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = 'bad file'
        try:
            oracles.soffice_to_csv(str(src))
            assert False, 'expected RuntimeError'
        except RuntimeError as e:
            assert 'conversion failed' in str(e)


# ── audit_ooxml ──────────────────────────────────────────────────────────

def test_audit_ooxml_absent_module(monkeypatch):
    monkeypatch.setattr(oracles, '_get_openxml_audit', lambda: None)
    assert oracles.audit_ooxml('/tmp/x.xlsx') is None


def test_audit_ooxml_valid(monkeypatch):
    class FakeResult:
        valid = True
        errors = []

    monkeypatch.setattr(oracles, '_get_openxml_audit',
                        lambda: type('m', (), {'validate': lambda p: FakeResult()}))
    result = oracles.audit_ooxml('/tmp/x.xlsx')
    assert result == {'valid': True, 'errors': []}


def test_audit_ooxml_invalid(monkeypatch):
    class FakeResult:
        valid = False
        errors = ['broken sheet']

    monkeypatch.setattr(oracles, '_get_openxml_audit',
                        lambda: type('m', (), {'validate': lambda p: FakeResult()}))
    result = oracles.audit_ooxml('/tmp/x.xlsx')
    assert result == {'valid': False, 'errors': ['broken sheet']}


# ── assert_matches_oracle ────────────────────────────────────────────────

def test_assert_matches_oracle_csv_contains(monkeypatch, tmp_path):
    src = tmp_path / 'book.xlsx'
    src.write_bytes(b'x')
    monkeypatch.setattr(oracles, 'soffice_to_csv',
                        lambda p: (str(tmp_path / 'book.csv'), 'alpha beta gamma'))
    # Should not raise.
    oracles.assert_matches_oracle(str(src), {'values_contain': ['alpha', 'gamma']})


def test_assert_matches_oracle_csv_asserts(monkeypatch, tmp_path):
    src = tmp_path / 'book.xlsx'
    src.write_bytes(b'x')
    monkeypatch.setattr(oracles, 'soffice_to_csv',
                        lambda p: (str(tmp_path / 'book.csv'), 'alpha beta'))
    try:
        oracles.assert_matches_oracle(str(src), {'values_contain': ['zzz']})
        assert False, 'expected AssertionError'
    except AssertionError as e:
        assert 'expected' in str(e)


def test_assert_matches_oracle_skips_when_soffice_missing(monkeypatch, tmp_path):
    src = tmp_path / 'book.xlsx'
    src.write_bytes(b'x')
    monkeypatch.setattr(oracles, 'soffice_to_csv',
                        lambda p: (_ for _ in ()).throw(RuntimeError('no soffice')))
    # Missing tool → check skipped silently.
    oracles.assert_matches_oracle(str(src), {'values_contain': ['zzz']})


def test_assert_matches_oracle_ooxml_valid(monkeypatch, tmp_path):
    src = tmp_path / 'book.xlsx'
    src.write_bytes(b'x')
    monkeypatch.setattr(oracles, 'soffice_to_csv',
                        lambda p: (_ for _ in ()).throw(RuntimeError('no soffice')))
    monkeypatch.setattr(oracles, 'audit_ooxml',
                        lambda p: {'valid': True, 'errors': []})
    oracles.assert_matches_oracle(str(src), {'ooxml_valid': True})


def test_assert_matches_oracle_ooxml_invalid_asserts(monkeypatch, tmp_path):
    src = tmp_path / 'book.xlsx'
    src.write_bytes(b'x')
    monkeypatch.setattr(oracles, 'soffice_to_csv',
                        lambda p: (_ for _ in ()).throw(RuntimeError('no soffice')))
    monkeypatch.setattr(oracles, 'audit_ooxml',
                        lambda p: {'valid': True, 'errors': []})
    try:
        oracles.assert_matches_oracle(str(src), {'ooxml_valid': False})
        assert False, 'expected AssertionError'
    except AssertionError:
        pass


# ── tools_available ──────────────────────────────────────────────────────

def test_tools_available(monkeypatch):
    monkeypatch.setattr(oracles, '_soffice', lambda: '/usr/bin/soffice')
    monkeypatch.setattr(oracles, '_get_openxml_audit', lambda: object())
    avail = oracles.tools_available()
    assert avail == {'soffice': True, 'openxml_audit': True}
