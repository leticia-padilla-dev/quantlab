# Paper: Alert Taxonomy and Failure Mapping

Issue: [#760](https://github.com/Whiteks1/quantlab/issues/760)

Status: docs-only. No runtime changes. No submit. Stage E remains blocked.

## Purpose

Define a deterministic mapping from:

- observed paper session states and artifact gaps
to:
- alert_code + severity + required operator action

This is an operator-facing contract. It is not a performance evaluation framework.

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Taxonomy Principles

```yaml
principles:
  - "alerts preserve historical evidence; latest success does not erase past critical alerts"
  - "critical implies stop"
  - "ambiguity implies stop"
  - "alerts must be explainable from canonical artifacts (no console archaeology)"
  - "paper alerts must not imply broker authority"
```

## Alert Severity Levels

```yaml
severity:
  ok:
    meaning: "No alerts triggered."
    action: "continue evidence capture only."
  warning:
    meaning: "Attention required; stop if ambiguity affects interpretability."
    action: "stop; reconcile artifacts; document if needed."
  critical:
    meaning: "Stop immediately; do not infer outcomes; do not continue operation."
    action: "stop; escalate; preserve evidence."
```

## Canonical Inputs

Primary:
- `session_status.json` (status, terminal flag, timestamps, error fields)

Supporting:
- `report.json`
- `trades.csv`
- `session_metadata.json`

Completeness and terminality rules:
- `docs/ops/paper-session-terminality-contract.md`
- `docs/ops/paper-artifact-completeness-contract.md`

## Current Implemented Alert Codes (Paper)

These codes are currently emitted by `--paper-sessions-alerts`:

```yaml
alert_codes:
  PAPER_SESSION_FAILED:
    severity: critical
    condition: "session_status.status == failed"
    operator_action: stop
  PAPER_SESSION_ABORTED:
    severity: warning
    condition: "session_status.status == aborted"
    operator_action: stop
  PAPER_SESSION_STALE:
    severity: warning
    condition: "session_status.status == running and age_minutes >= stale_after_minutes"
    operator_action: stop_and_escalate
```

## Proposed Additional Codes (Contract-first; may be implemented later)

```yaml
proposed_alert_codes:
  PAPER_ARTIFACT_INCOMPLETE:
    severity: critical
    condition: "required_minimum artifacts missing or not parseable"
    operator_action: stop
    evidence_required:
      - "missing session_status.json OR report.json OR trades.csv OR session_metadata.json"
  PAPER_TERMINALITY_INCONSISTENT:
    severity: critical
    condition: "session_status.terminal == true but required artifacts missing"
    operator_action: stop
  PAPER_STATUS_UNKNOWN:
    severity: critical
    condition: "session_status.status == unknown OR missing status"
    operator_action: stop
```

## Failure Mapping Table (Deterministic)

```yaml
failure_mapping:
  - observation: "status == failed"
    alert_code: PAPER_SESSION_FAILED
    severity: critical
    operator_action: stop
  - observation: "status == aborted"
    alert_code: PAPER_SESSION_ABORTED
    severity: warning
    operator_action: stop
  - observation: "status == running and stale"
    alert_code: PAPER_SESSION_STALE
    severity: warning
    operator_action: stop_and_escalate
  - observation: "terminal==true but report.json missing"
    alert_code: PAPER_ARTIFACT_INCOMPLETE
    severity: critical
    operator_action: stop
  - observation: "success but trades.csv missing"
    alert_code: PAPER_ARTIFACT_INCOMPLETE
    severity: critical
    operator_action: stop
  - observation: "status unknown or missing"
    alert_code: PAPER_STATUS_UNKNOWN
    severity: critical
    operator_action: stop
```

## Non-Goals

- This taxonomy does not grade strategy performance.
- This taxonomy does not authorize broker actions.
- This taxonomy does not open Stage E.
