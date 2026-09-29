# Suite-Common Observability & Operational Readiness Assessment

This document outlines the observability posture, diagnostic logging interfaces, and operational boundaries for `suite-common` (`tuna-os/suite-common`).

---

## 1. Context & Architecture

- **Component Name**: `suite-common` (`suite_common`)
- **Architecture**: Shared GTK4 / Libadwaita / WebKitGTK scaffold library written in Python 3.
- **Role**: Provides common window management (`SuiteWindow`), application lifecycle (`SuiteApplication`), WebKit IPC bridge (`SuiteWebView`), file I/O dispatch, and oracle test helpers.
- **Maintenance Status**: Legacy Python implementation in bugfix-only maintenance. Superceded by the Rust rewrite (`gtk-office-suite`).

---

## 2. Telemetry Boundaries & Data Policy

- **Managed Observability Target**: Zero external telemetry backends configured.
- **Data Boundary**: `suite-common` contains no remote telemetry exporters or external network data collection routines. All diagnostic logs remain strictly local to the user session.
- **Oracle & Conversion Dependencies**: Headless LibreOffice (`soffice`) and OpenXML audit helpers during offline test verification.

---

## 3. Diagnostic Signal Sources

### 3.1 GLib & GTK Log Domains
`suite-common` components emit diagnostic messages via standard `GLib` log channels. Consuming applications and developers inspect log output by setting debug environment variables:

```bash
# Enable all GLib debug messages
G_MESSAGES_DEBUG=all python3 -m unittest discover -s tests

# Filter for specific GTK/Adwaita or WebKit log domains
G_MESSAGES_DEBUG=Gtk,Adw,WebKitGTK python3 tests/test_fileio.py
```

### 3.2 WebKit IPC Diagnostic Bridge
The `SuiteWebView` module provides message passing between Python and JavaScript editor engines. Diagnostics for IPC message handling expose:
- Serialized message payloads and signal routing errors.
- WebProcess crash signals via WebKitGTK log channels.

---

## 4. Operational Health & Verification Criteria

| Interface / Surface | Health Signal | Verification Method |
| :--- | :--- | :--- |
| **Application Lifecycle** | `SuiteApplication` startup & shortcut binding | `python3 tests/test_shortcuts_presets.py` |
| **File I/O Base** | Format extension dispatch & mime detection | `python3 tests/test_fileio.py` |
| **Oracle Integration** | LibreOffice headless conversion capability | `python3 tests/test_oracles.py` |

---

## 5. Operations Recommendation Summary

1. **Diagnostic Flags**: Use `G_MESSAGES_DEBUG=all` for GTK4/Adwaita UI widget and WebKit IPC debugging.
2. **Offline Verification**: Retain oracle test suites (`test_oracles.py`) to verify document format fidelity during bugfix maintenance.
3. **Upstream Migration**: Route new feature work or monorepo enhancements to `tuna-os/gtk-office-suite`.
