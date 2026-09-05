name: Operational Incident Report
description: Report an operational defect, test suite failure, or dependency breakage in suite-common.
title: "[incident] "
labels: ["incident", "operations"]
body:
  - type: markdown
    attributes:
      value: |
        Use this template to report operational issues, test suite failures, or GTK4/WebKit binding breakages in suite-common.

  - type: dropdown
    id: severity
    attributes:
      label: Incident Severity
      options:
        - Critical (Core scaffold crash, widespread test failure)
        - Major (Webview / File I/O regression)
        - Minor (Non-blocking warning or minor test flaw)
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: Incident Description
      description: Detailed description of the operational issue.
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Terminal Logs & Error Output
      description: Paste relevant Python tracebacks, GLib debug outputs, or test failure logs.
      render: shell
    validations:
      required: false

  - type: textarea
    id: environment
    attributes:
      label: Execution Environment
      description: OS version, Python version, PyGObject / GTK4 versions.
    validations:
      required: true
