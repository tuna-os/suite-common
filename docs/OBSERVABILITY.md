# Observability Assessment & Telemetry Guidelines: suite-common

This document assesses the telemetry and diagnostic architecture of `suite-common` (Python GNOME desktop application scaffold) and defines local telemetry guidelines in compliance with TunaOS telemetry policies.

---

## 1. Executive Summary & Stack Assessment

- **Application Type**: Shared Python Library / Scaffold (PyGObject, GTK4, Libadwaita).
- **Configured Telemetry Backend**: **None (Unconfigured)**.
- **Current Data Flows**: Local Python execution and GTK4 event dispatching across applications importing `suite_common`.
- **Policy Enforcement**: Because no backend collector or server is explicitly configured, `suite-common` operates in **audit-only mode**. No external exporters, network telemetry, or telemetry dependencies (e.g. OpenTelemetry SDKs, GA4 scripts) may be added to shared scaffold components.

---

## 2. Existing Diagnostic Subsystems

`suite-common` provides shared application bases and window components that interact with GLib/GTK logging and standard error output streams:

### 2.1 Python Logging Subsystem
- Standard library `logging` module initialized within shared application wrappers.
- Standard error (`sys.stderr`) output stream.

### 2.2 GLib & GTK Diagnostic Environment Variables
- `G_MESSAGES_DEBUG`: Enable GLib debug log filtering across applications using `suite_common`.
- `GTK_DEBUG`: Enable GTK widget, rendering, or accessibility diagnostic logging.

---

## 3. Data Privacy & Local Boundary Guidelines

1. **No External Egress**: Telemetry data from applications leveraging `suite-common` must never be transmitted off-device without explicit operator configuration.
2. **PII and Sensitive Data Protection**: Document content, file paths, user configuration entries, and environment variables must be excluded from diagnostic logging.
3. **Bounded Metrics & Logging**: Any future shared metrics or log helper functions in `suite-common` must maintain strict limits on metric label cardinality.

---

## 4. Operational Runbook & Future Telemetry Roadmap

If an operator explicitly configures an OpenTelemetry or Prometheus collector in applications using `suite-common`:
- Provide opt-in, non-blocking telemetry provider wrappers within `suite_common`.
- Enforce strict validation ensuring zero data egress when unconfigured.
