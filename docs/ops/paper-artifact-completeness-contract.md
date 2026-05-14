# Paper: Artifact Completeness Contract

Issue: [#758](https://github.com/Whiteks1/quantlab/issues/758)

Status: docs-only. No runtime changes. No submit. Stage E remains blocked.

## Purpose

Paper sessions are only actionable as evidence if their artifacts are complete enough for deterministic interpretation.

This contract defines:

- the canonical paper-session artifact pack
- completeness levels
- how missing artifacts map to severity and stop rules

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Canonical Paper Session Root

```text
outputs/paper_sessions/<session_id>/
```

## Required Artifacts (Minimum)

These are required to claim a paper session is interpretable:

```yaml
required_minimum:
  - session_metadata.json
  - session_status.json
  - report.json
  - trades.csv
```

Meaning:
- `session_status.json` provides lifecycle truth (terminality, status, errors).
- `report.json` provides canonical machine contract output.
- `trades.csv` provides the trade trace (even if empty).
- `session_metadata.json` anchors identity (session id, request id, timestamps).

## Recommended Artifacts (Strong Evidence Pack)

```yaml
recommended:
  - config.json
  - metrics.json
  - run_report.md
  - artifacts/  # auxiliary outputs
```

## Completeness Levels

```yaml
completeness_levels:
  A_minimum_interpretable:
    description: "All required_minimum artifacts exist and parse."
    allowed_actions:
      - continue_evidence_capture
    forbidden_actions:
      - infer_missing_fields_from_logs
  B_strong_evidence_pack:
    description: "required_minimum + recommended artifacts exist."
    allowed_actions:
      - compare_sessions_for_operational_repeatability
  C_incomplete:
    description: "Any required_minimum artifact missing or not parseable."
    allowed_actions:
      - stop
      - escalate
```

## Severity Mapping (Deterministic)

```yaml
severity_mapping:
  - condition: "session_status.json missing OR not parseable"
    severity: critical
    action: stop
  - condition: "session_status.terminal == true AND report.json missing"
    severity: critical
    action: stop
  - condition: "session_status.status == success AND trades.csv missing"
    severity: critical
    action: stop
  - condition: "session_status.status in [failed, aborted] AND error fields missing"
    severity: warning
    action: stop
  - condition: "config.json missing OR metrics.json missing"
    severity: warning
    action: continue_evidence_capture
```

## Operator Checklist (Copy/Paste)

```yaml
paper_artifact_completeness_review:
  session_id: "<paper_session_id>"
  required_minimum:
    session_metadata_json: true
    session_status_json: true
    report_json: true
    trades_csv: true
  recommended:
    config_json: false
    metrics_json: false
    run_report_md: false
  completeness_level: A_minimum_interpretable
  severity: ok
  next_action: continue_evidence_capture
```

## Non-Goals

- This contract does not authorize broker actions.
- This contract does not authorize submit retries.
- This contract does not open Stage E.
