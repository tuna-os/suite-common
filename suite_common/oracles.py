# Test oracle helpers — independent verification via LibreOffice headless +
# openxml-audit.  See TESTING-SPEC.md §2 / §4b.
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import subprocess
import tempfile


# ── LibreOffice headless ───────────────────────────────────────────────

_SOFFICE = os.environ.get('SOFFICE', 'soffice')


def _soffice():
    """Return the path to soffice, or None if unavailable."""
    try:
        subprocess.run([_SOFFICE, '--version'], capture_output=True,
                       timeout=10, check=True)
        return _SOFFICE
    except Exception:
        return None


def soffice_to_csv(in_path):
    """Convert a spreadsheet to CSV via LibreOffice headless.

    Returns (path_to_csv, csv_text) or raises RuntimeError if soffice
    is unavailable or conversion fails.
    """
    soffice = _soffice()
    if soffice is None:
        raise RuntimeError('soffice not found — install libreoffice-core-nogui')
    with tempfile.TemporaryDirectory() as td:
        out_dir = td
        args = [soffice, '--headless', '--convert-to', 'csv',
                '--outdir', out_dir, in_path]
        proc = subprocess.run(args, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            raise RuntimeError(f'soffice csv conversion failed: {proc.stderr}')
        # soffice names output after the input stem + .csv in out_dir
        stem = os.path.splitext(os.path.basename(in_path))[0]
        csv_path = os.path.join(out_dir, stem + '.csv')
        if not os.path.exists(csv_path):
            # Some versions append sheet index
            for candidate in os.listdir(out_dir):
                if candidate.startswith(stem) and candidate.endswith('.csv'):
                    csv_path = os.path.join(out_dir, candidate)
                    break
        if not os.path.exists(csv_path):
            raise RuntimeError(f'soffice produced no csv in {out_dir}')
        with open(csv_path, encoding='utf-8', errors='replace') as fh:
            text = fh.read()
        return csv_path, text


def soffice_to_fodp(in_path):
    """Convert a presentation to flat ODP XML (fodp) via LibreOffice headless.

    Returns (path_to_fodp, xml_text).
    """
    soffice = _soffice()
    if soffice is None:
        raise RuntimeError('soffice not found — install libreoffice-core-nogui')
    with tempfile.TemporaryDirectory() as td:
        args = [soffice, '--headless', '--convert-to', 'fodp',
                '--outdir', td, in_path]
        proc = subprocess.run(args, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            raise RuntimeError(f'soffice fodp conversion failed: {proc.stderr}')
        stem = os.path.splitext(os.path.basename(in_path))[0]
        fodp_path = os.path.join(td, stem + '.fodp')
        if not os.path.exists(fodp_path):
            raise RuntimeError(f'soffice produced no fodp in {td}')
        with open(fodp_path, encoding='utf-8', errors='replace') as fh:
            text = fh.read()
        return fodp_path, text


# ── openxml-audit ──────────────────────────────────────────────────────

_OPENXML_AUDIT = None


def _get_openxml_audit():
    """Lazy-import openxml-audit; returns the module or None."""
    global _OPENXML_AUDIT
    if _OPENXML_AUDIT is False:
        return None
    if _OPENXML_AUDIT is None:
        try:
            import openxml_audit  # noqa: F811
            _OPENXML_AUDIT = openxml_audit
        except ImportError:
            _OPENXML_AUDIT = False
    return _OPENXML_AUDIT if _OPENXML_AUDIT is not False else None


def audit_ooxml(path):
    """Validate an OOXML file (xlsx/pptx) with openxml-audit.

    Returns a dict with keys 'valid' (bool) and 'errors' (list of str).
    Returns None if openxml-audit is not installed.
    """
    m = _get_openxml_audit()
    if m is None:
        return None
    result = m.validate(path)
    return {
        'valid': result.valid if hasattr(result, 'valid') else not result.errors,
        'errors': list(result.errors) if hasattr(result, 'errors') else [],
    }


# ── Oracle assertion helper ────────────────────────────────────────────

def assert_matches_oracle(path, expectations):
    """Verify a saved office file against independent oracles.

    ``expectations`` is a dict with keys:

    - ``values_contain`` (str | list[str]): substrings expected in CSV output.
    - ``values_not_contain`` (str | list[str]): substrings that must NOT appear.
    - ``fodp_contain`` (str | list[str]): substrings expected in flat ODP.
    - ``ooxml_valid`` (bool): whether openxml-audit should pass.

    Each check is skipped silently if the required tool is unavailable.
    """
    if isinstance(expectations.get('values_contain'), str):
        expectations['values_contain'] = [expectations['values_contain']]
    if isinstance(expectations.get('values_not_contain'), str):
        expectations['values_not_contain'] = [expectations['values_not_contain']]
    if isinstance(expectations.get('fodp_contain'), str):
        expectations['fodp_contain'] = [expectations['fodp_contain']]

    ext = os.path.splitext(path)[1].lower()

    # Spreadsheet: convert to CSV + assert values
    if ext in ('.xlsx', '.ods', '.csv'):
        try:
            _, csv_text = soffice_to_csv(path)
        except RuntimeError:
            pass  # soffice unavailable — skip
        else:
            for substr in expectations.get('values_contain') or []:
                assert substr in csv_text, \
                    f'oracle csv: expected "{substr}" not found in {path}'
            for substr in expectations.get('values_not_contain') or []:
                assert substr not in csv_text, \
                    f'oracle csv: unexpected "{substr}" found in {path}'

    # Presentation: convert to flat ODP + assert text
    if ext in ('.pptx', '.odp'):
        try:
            _, fodp_text = soffice_to_fodp(path)
        except RuntimeError:
            pass
        else:
            for substr in expectations.get('fodp_contain') or []:
                assert substr in fodp_text, \
                    f'oracle fodp: expected "{substr}" not found in {path}'

    # OOXML structural validation
    if ext in ('.xlsx', '.pptx') and 'ooxml_valid' in expectations:
        result = audit_ooxml(path)
        if result is not None:
            if expectations['ooxml_valid']:
                assert result['valid'], \
                    f'openxml-audit: {path} has errors: {result["errors"]}'
            else:
                assert not result['valid'], \
                    f'openxml-audit: {path} unexpectedly valid'


# ── Tool availability probes ───────────────────────────────────────────

def tools_available():
    """Return a dict describing which oracle tools are available."""
    return {
        'soffice': _soffice() is not None,
        'openxml_audit': _get_openxml_audit() is not None,
    }
