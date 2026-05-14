# Paper: Failure Retention and Alert Horizon Policy

Status: docs-only. No runtime changes. No submit. Stage E remains blocked.

## Purpose

QuantLab paper operations must satisfy two needs simultaneously:

- preserve historical evidence and avoid hiding failures
- avoid having old failures permanently dominate the operator’s current operational read

This policy defines:

- what is retained (always)
- what is surfaced as critical now (horizon/window)
- how “current operational window” is separated from “historical aggregate health”

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Non-Negotiables

```yaml
do_not:
  - delete_old_failures
  - hide_critical_history
  - mark_failed_as_success
  - weaken_alerts_to_get_green
```

## Definitions

Canonical paper truth:

- per-session artifacts under `outputs/paper_sessions/<session_id>/`
- terminality, completeness, and deterministic interpretation per P0 contracts

Observability:

- aggregated summaries over `outputs/paper_sessions/`
- deterministic projections that must not overwrite canonical truth

## Retention Policy (Evidence)

```yaml
retention:
  canonical_artifacts:
    policy: retain_indefinitely
    scope:
      - outputs/paper_sessions/<session_id>/**
  aggregate_artifacts:
    policy: append_only
    scope:
      - outputs/paper_sessions/paper_sessions_health.json
      - outputs/paper_sessions/paper_sessions_alerts.json
      - outputs/paper_sessions/paper_sessions_index.json
      - outputs/paper_sessions/paper_sessions_index.csv
```

Rationale:

- paper is an evidence system; deleting failures breaks auditability
- historical failures must remain reviewable for operational learning

## Horizon Policy (Operator Read)

This policy introduces the concept of a current operational horizon.

### Horizon types

```yaml
horizon_types:
  by_time:
    example: "last 7 days"
  by_count:
    example: "last 20 sessions"
  by_both:
    example: "last 7 days AND last 20 sessions"
```

### What horizon affects

Horizon affects only:

- which sessions contribute to the “current_window_alert_status”
- which alerts are included in a “current_window_alerts[]” list

Horizon must not affect:

- canonical truth of any session
- historical aggregate health and alert visibility

## Required Aggregate Outputs (Two-Layer)

The observability layer must surface both:

```yaml
observability_layers:
  historical:
    intent: "long-term audit visibility"
    computed_over: "all sessions in outputs/paper_sessions/"
  current_window:
    intent: "operator's current operational read"
    computed_over: "sessions filtered by the horizon policy"
```

Operator rule:

- current_window may be green while historical remains critical
- historical must remain visible even when current_window is healthy

## Default Horizon Recommendation (for local operators)

This repo should converge on a default that is conservative and deterministic:

```yaml
default_horizon:
  mode: by_both
  last_days: 7
  max_sessions: 20
```

Reasoning:

- avoids indefinite red due to very old failures
- still preserves recent operational truth
- still preserves historical visibility

## Escalation Semantics

```yaml
escalation:
  if_current_window_is_critical:
    action: stop
  if_current_window_is_warning:
    action: stop_and_classify
  if_current_window_is_ok_but_historical_is_critical:
    action: proceed_with_caution_and_document_that_history_is_critical
```

Operator interpretation rules:

- [paper-alert-posture-interpretation-rules.md](./paper-alert-posture-interpretation-rules.md)

## Follow-Up Implementation Notes (Out of Scope for This Doc)

Runtime work should remain additive and report-only:

- an explicit CLI flag to compute current window, e.g. `--paper-alert-window-days` / `--paper-alert-window-sessions`
- aggregate artifacts extended to include:
  - `historical_alert_status`
  - `current_window_alert_status`
  - `current_window_horizon`
  - separate `historical_alerts[]` vs `current_window_alerts[]`

No automatic remediation:

- no retry loops
- no deletion
- no auto-hiding
