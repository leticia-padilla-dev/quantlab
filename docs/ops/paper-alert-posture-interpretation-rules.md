# Paper: Operator Interpretation Rules for Alert Posture

Issue: [#779](https://github.com/Whiteks1/quantlab/issues/779)

Status: docs-only. No runtime changes. No submit. Stage E remains blocked.

## Purpose

This document defines a deterministic procedure for interpreting the paper alert posture produced by:

- `python main.py --paper-sessions-alerts outputs/paper_sessions ...`
- `outputs/paper_sessions/paper_sessions_alerts.json` (when present)

Goal:

- Two operators reach the same decision about whether to stop, classify, or proceed with evidence capture.

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Inputs (Authoritative for Posture)

The posture decision is based on the alert snapshot JSON, which contains:

- historical posture over all sessions:
  - `alert_status`
  - `alerts[]`
- current operational window posture over a horizon-filtered subset:
  - `horizon`
  - `current_window_alert_status`
  - `current_window_alerts[]`

The alert snapshot is an observability projection. It must not overwrite or replace canonical per-session truth.

If posture is ambiguous, the operator must fall back to canonical artifacts under:

- `outputs/paper_sessions/<session_id>/session_status.json`
- `outputs/paper_sessions/<session_id>/session_metadata.json`
- `outputs/paper_sessions/<session_id>/report.json`

## Definitions

Historical posture:

- Computed over all known sessions under `outputs/paper_sessions/`.
- Must remain visible even when the current operational window is healthy.

Current operational window posture:

- Computed over the intersection of:
  - sessions within `horizon.window_days` of `generated_at`
  - the latest `horizon.window_sessions` sessions by activity
- Used as the operator's current operational read.

Governing policy:

- [paper-failure-retention-and-alert-horizon-policy.md](./paper-failure-retention-and-alert-horizon-policy.md)

Operator declaration surface:

- [paper-alert-posture-operator-declaration.md](./paper-alert-posture-operator-declaration.md)

## Decision Procedure (Deterministic)

### Step 0 — Generate or load the snapshot

Preferred:

- run `--paper-sessions-alerts` with explicit horizon flags
- persist the JSON output as evidence

Acceptable (when already present):

- read `outputs/paper_sessions/paper_sessions_alerts.json`

### Step 1 — Schema presence gate (stop-on-ambiguity)

If any of these are missing, treat posture as ambiguous and stop:

- `generated_at`
- `alert_status`
- `alerts`
- `horizon`
- `current_window_alert_status`
- `current_window_alerts`

Output:

```yaml
alert_posture_conclusion:
  posture: ambiguous
  next_action: stop
  rationale: "missing required fields in paper_sessions_alerts snapshot"
```

### Step 2 — Current window gate (primary operational read)

Rules:

```yaml
current_window_rules:
  - if: "current_window_alert_status == critical"
    then: { posture: critical, next_action: stop }
  - if: "current_window_alert_status == warning"
    then: { posture: warning, next_action: stop_and_classify }
  - if: "current_window_alert_status == ok"
    then: { posture: ok, next_action: proceed }
```

### Step 3 — Historical visibility rule (must remain explicit)

Historical posture does not override the current window gate, but it must be recorded:

```yaml
historical_visibility:
  - if: "alert_status == critical and current_window_alert_status == ok"
    then: { historical_posture_note: "historical_is_critical", next_action: proceed_with_caution_and_record }
  - if: "alert_status == warning and current_window_alert_status == ok"
    then: { historical_posture_note: "historical_is_warning", next_action: proceed_with_caution_and_record }
```

Operator rule:

- do not hide or delete failures to change historical posture
- current window may be green while historical remains critical

### Step 4 — Minimum classification when stopping

When the procedure yields `stop` or `stop_and_classify`, the operator must record:

- horizon used (`horizon.mode`, `horizon.window_days`, `horizon.window_sessions`)
- the latest current-window alert (if present)
- the session_id(s) implicated by current window alerts

Then classify each implicated session by inspecting its canonical artifact pack.

## Classification Template (copy/paste)

```yaml
alert_posture_conclusion:
  generated_at: "<snapshot.generated_at>"
  horizon:
    mode: "<snapshot.horizon.mode>"
    window_days: <snapshot.horizon.window_days>
    window_sessions: <snapshot.horizon.window_sessions>
  historical:
    alert_status: "<snapshot.alert_status>"
    alert_counts: "<snapshot.alert_counts>"
  current_window:
    alert_status: "<snapshot.current_window_alert_status>"
    alert_counts: "<snapshot.current_window_alert_counts>"
    latest_alert:
      session_id: "<snapshot.current_window_latest_alert_session_id>"
      code: "<snapshot.current_window_latest_alert_code>"
      at: "<snapshot.current_window_latest_alert_at>"
  next_action: proceed | proceed_with_caution_and_record | stop | stop_and_classify
  notes: ""
```

## Non-Goals

- This does not authorize broker actions.
- This does not authorize retries or auto-remediation.
- This does not open Stage E.
