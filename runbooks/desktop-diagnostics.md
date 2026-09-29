# Desktop Diagnostics & Operational Runbook — Suite-Common

This runbook details diagnostic procedures, troubleshooting steps, and resolution paths for the `suite-common` shared GTK4 scaffold library.

---

## 1. Triage Workflow

```
[Issue / Test Failure Reported]
              │
              ▼
1. Validate Python Environment & GTK4 Bindings
              │
              ▼
2. Inspect GLib & WebKitGTK Debug Log Outputs
              │
              ▼
3. Verify File I/O & Oracle Subprocess Dependencies
              │
              ▼
4. Remediate Environment or Test Fixtures
```

---

## 2. Standard Triage Procedures

### Step 1: Environment & Dependency Verification
Verify PyGObject, GTK4, and Libadwaita bindings in the execution environment:

```bash
python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1'); from gi.repository import Gtk, Adw; print('GTK4 & Adwaita available')"
```

### Step 2: Diagnostic Logging
Run unit tests with full GLib debugging enabled:

```bash
G_MESSAGES_DEBUG=all python3 -m unittest discover -s tests
```

---

## 3. Failure Modes & Resolution Steps

### Failure Mode 1: WebKit Process Crashes in `SuiteWebView`

* **Symptom**: WebKit view fails to render or emits `WebProcess crashed` signals.
* **Root Cause**: GPU acceleration incompatibility or WebKitGTK sandbox environment restrictions.
* **Diagnostic Steps**:
  1. Test with WebKit compositing disabled:
     ```bash
     WEBKIT_DISABLE_COMPOSITING_MODE=1 python3 -m unittest tests/test_shortcuts_presets.py
     ```
  2. Inspect stderr output for GLib-GIO error tracebacks.
* **Remediation**: Set `WEBKIT_DISABLE_COMPOSITING_MODE=1` in headless CI or restricted container environments.

---

### Failure Mode 2: Oracle Conversion Failures (`test_oracles.py`)

* **Symptom**: Oracle tests fail during document verification.
* **Root Cause**: Missing LibreOffice (`soffice`) binary or incompatible document filter libraries.
* **Diagnostic Steps**:
  1. Check `soffice` executable in system PATH:
     ```bash
     which soffice || libreoffice --version
     ```
  2. Run oracle tests directly:
     ```bash
     python3 tests/test_oracles.py
     ```
* **Remediation**: Install LibreOffice package (`libreoffice-calc`, `libreoffice-writer`) in testing environment.

---

### Failure Mode 3: Shortcut Preset Binding Failures

* **Symptom**: Keyboard shortcuts (Ctrl+O, Ctrl+S, Ctrl+P) fail to trigger application actions.
* **Root Cause**: GActionMap keyval collision or missing `Adw.Application` initialization.
* **Diagnostic Steps**:
  1. Run shortcut preset unit tests:
     ```bash
     python3 tests/test_shortcuts_presets.py
     ```
  2. Verify action group registration in `SuiteApplication`.

---

## 4. Maintenance & Bugfix Policy

Since `suite-common-python` is in **bugfix-only maintenance**:
- Focus changes on fixing crash defects, regression bugs, and test suite stability.
- New scaffold features or monorepo improvements should be contributed to `tuna-os/gtk-office-suite`.
