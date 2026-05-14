# Paper: Alert Posture Operator Declaration

Issue: [#788](https://github.com/Whiteks1/quantlab/issues/788)

Status: docs-only. No runtime changes. No submit. Stage E remains blocked.

## Purpose

This declaration is a signable operator artifact.

It records:

- which alert horizon was used for the operational window
- the observed posture (historical vs current window)
- the deterministic next action the operator commits to taking

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Commands (Required)

Run these commands from the repo root.

Health (human-readable):

```bash
python main.py --paper-sessions-health outputs/paper_sessions
```

Alerts (machine-readable; recommended default horizon):

```bash
python main.py --paper-sessions-alerts outputs/paper_sessions \
  --paper-stale-minutes 60 \
  --paper-alert-window-days 7 \
  --paper-alert-window-sessions 20
```

If you need to reduce noise for the current operational window, you may tighten the horizon and capture an additional snapshot, for example:

```bash
python main.py --paper-sessions-alerts outputs/paper_sessions \
  --paper-stale-minutes 60 \
  --paper-alert-window-days 1 \
  --paper-alert-window-sessions 5
```

## Required Attachments (Local, Not Versioned)

Persist the outputs as local evidence under `outputs/` (not committed), for example:

- `outputs/ops_drills/<drill_id>/paper_sessions_health.txt`
- `outputs/ops_drills/<drill_id>/paper_sessions_alerts_horizon_7d_20s.json`
- `outputs/ops_drills/<drill_id>/paper_sessions_alerts_horizon_1d_5s.json` (optional)

If the operator stops, also list the implicated session directories:

- `outputs/paper_sessions/<session_id>/...`

## Decision Rule (Deterministic)

Interpretation source of truth:

- [paper-alert-posture-interpretation-rules.md](./paper-alert-posture-interpretation-rules.md)

Summary:

- If `current_window_alert_status` is `critical`: stop.
- If `current_window_alert_status` is `warning`: stop and classify.
- If `current_window_alert_status` is `ok` and historical is `critical`: proceed with caution and explicitly record that historical remains critical.

Non-negotiable:

- Do not delete failures or rewrite history to change posture.

## Declaration Template (copy/paste)

```yaml
paper_alert_posture_declaration:
  date: YYYY-MM-DD
  operator: "<name or handle>"
  scope:
    paper_only: true
    broker_actions: false
    submit_allowed: false
    stage_e: blocked

  inputs:
    paper_root: "outputs/paper_sessions"
    stale_after_minutes: 60
    horizon:
      mode: and
      window_days: 7
      window_sessions: 20

  evidence:
    drill_outputs_root: "outputs/ops_drills/<drill_id>"
    health_output: "outputs/ops_drills/<drill_id>/paper_sessions_health.txt"
    alert_snapshot: "outputs/ops_drills/<drill_id>/paper_sessions_alerts_horizon_7d_20s.json"
    optional_additional_snapshots: []
    implicated_sessions: []

  observed_posture:
    historical:
      alert_status: "<snapshot.alert_status>"
      alert_counts: "<snapshot.alert_counts>"
      latest_alert_session_id: "<snapshot.latest_alert_session_id>"
      latest_alert_code: "<snapshot.latest_alert_code>"
    current_window:
      alert_status: "<snapshot.current_window_alert_status>"
      alert_counts: "<snapshot.current_window_alert_counts>"
      latest_alert_session_id: "<snapshot.current_window_latest_alert_session_id>"
      latest_alert_code: "<snapshot.current_window_latest_alert_code>"

  decision:
    next_action: proceed | proceed_with_caution_and_record | stop | stop_and_classify
    rationale: ""
```

## Non-Goals

- This does not authorize any broker action.
- This does not open Stage E.
- This does not add automation or retry behavior.
