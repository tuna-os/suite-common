name: Incident Postmortem
description: Document root cause analysis and action items following an operational incident in suite-common.
title: "[postmortem] "
labels: ["postmortem", "operations"]
body:
  - type: markdown
    attributes:
      value: |
        Use this template to document postmortem analysis for resolved operational incidents.

  - type: textarea
    id: summary
    attributes:
      label: Executive Summary
      description: Overview of the incident, impact, and final resolution.
    validations:
      required: true

  - type: textarea
    id: root_cause
    attributes:
      label: Root Cause Analysis
      description: Technical root cause and contributing factors.
    validations:
      required: true

  - type: textarea
    id: timeline
    attributes:
      label: Timeline of Events
      description: Detection, triage, mitigation, and resolution timeline.
    validations:
      required: true

  - type: textarea
    id: action_items
    attributes:
      label: Action Items & Follow-up Safeguards
      description: List preventive measures, test additions, or documentation updates.
    validations:
      required: true
