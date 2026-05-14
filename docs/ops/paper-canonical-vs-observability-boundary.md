# Paper: Canonical State vs Observability Layer Boundary

Issue: [#761](https://github.com/Whiteks1/quantlab/issues/761)

Status: docs-only. No runtime changes. No submit. Stage E remains blocked.

## Purpose

QuantLab paper operations rely on two layers:

- canonical state: what the session is, as proven by per-session artifacts
- observability layer: aggregated health/alerts views over many sessions

This document fixes the boundary between them to prevent semantic drift:

- observability must never overwrite canonical truth
- observability may elevate severity and force stop, but cannot fabricate terminality

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Canonical Layer (Per-Session)

Canonical state is derived only from:

```text
outputs/paper_sessions/<session_id>/
  session_status.json
  session_metadata.json
  report.json
  trades.csv
```

Canonical conclusions must follow:

- `docs/ops/paper-session-terminality-contract.md`
- `docs/ops/paper-artifact-completeness-contract.md`
- `docs/ops/paper-operator-interpretation-contract.md`

### Canonical outputs

```yaml
canonical_outputs:
  terminality: terminal | non_terminal
  terminal_category: completed | failed | aborted | rejected
  completeness_level: A_minimum_interpretable | B_strong_evidence_pack | C_incomplete
  required_operator_action: continue_evidence_capture | stop | escalate
```

## Observability Layer (Aggregates)

Observability is derived from aggregations over:

- `outputs/paper_sessions/` (root)

Examples:

- health summaries (counts, latest sessions, active sessions)
- alert snapshots (failed/aborted/stale classification)

### Observability outputs

```yaml
observability_outputs:
  root_alert_status: ok | warning | critical
  alerts:
    - alert_code
    - severity
    - activity_at
    - session_id
    - message
```

## Non-Overridable Boundary Rules

```yaml
boundary_rules:
  - rule: "observability must not change per-session canonical artifacts"
  - rule: "observability must not infer success if canonical artifacts are missing"
  - rule: "observability may elevate severity to warning/critical based on missingness or staleness"
  - rule: "canonical terminality is the only source of 'terminal vs non_terminal'"
  - rule: "missing canonical artifacts implies stop, not optimistic continuation"
```

## Practical Examples (Deterministic)

### Example 1 — Root alert critical, latest session success

This is permitted and expected:

- root alert status is derived across history (preserves prior failures)
- latest session may still be terminal and successful

Operator rule:

- do not treat latest success as clearing historical alerts
- continue evidence capture only for sessions proven terminal and complete

### Example 2 — Health says "latest session success" but report.json missing

This must be treated as ambiguous:

- canonical layer: non_terminal (completeness violation)
- observability layer: may show warning/critical

Operator rule:

- stop and treat as incomplete evidence pack

## Non-Goals

- This document does not redefine how sessions are produced.
- This document does not authorize broker actions.
- This document does not open Stage E.
