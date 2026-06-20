# Paper-Live Session 01 - Failed Controlled Attempt

Issue: [#816](https://github.com/leticia-padilla-dev/quantlab/issues/816)

Status: evidence memo. One supervised paper-live attempt was executed. No retry.

## Summary

```yaml
paper_live_session_01:
  session_id: 20260620_073810_paper_7075f45
  result: failed_controlled
  terminal_status: failed
  status_reason: exception
  error_type: DataError
  error_message: "No data remaining after applying indicators (need more history for lookbacks)."
  retry_performed: false
  second_paper_run_performed: false
  broker_submit: false
  live_capital: false
  stage_e: blocked
  automation: false
```

The first supervised paper-live session did not validate the happy path. It did
validate the operational discipline required by the protocol: the operator
stopped after the first failed attempt and did not rerun with a wider window.

## Command Used

```powershell
.\.venv\Scripts\python.exe main.py --ticker ETH-USD --start 2026-06-10 --end 2026-06-17 --paper --report --initial_cash 10000
```

## Session Path

```text
outputs/paper_sessions/20260620_073810_paper_7075f45
```

## Configuration

```yaml
config:
  ticker: ETH-USD
  start: "2026-06-10"
  end: "2026-06-17"
  interval: 1d
  paper: true
  initial_cash: 10000.0
  fee: 0.002
  slippage_mode: fixed
  slippage_bps: 8.0
  k_atr: 0.05
  rsi_buy_max: 60.0
  rsi_sell_min: 75.0
  cooldown_days: 0
```

## Artifact Inventory

Present:

```yaml
present_artifacts:
  - artifacts/
  - config.json
  - metadata.json
  - session_metadata.json
  - session_status.json
```

Missing:

```yaml
missing_artifacts:
  - report.json
  - metrics.json
  - trades.csv
  - run_report.md
```

Interpretation:

- Missing report/metrics/trades artifacts are expected for this failure point.
- The session failed before the data survived indicator lookbacks and before a
  complete paper result could be materialized.

## Session Status

```yaml
session_status:
  command: paper
  mode: paper
  status: failed
  status_reason: exception
  terminal: true
  error_type: DataError
  message: "No data remaining after applying indicators (need more history for lookbacks)."
  started_at: "2026-06-20T09:38:10.457992"
  updated_at: "2026-06-20T09:38:11.013087"
  finished_at: "2026-06-20T09:38:11.013087"
  duration_seconds: 0.555095
```

## Health Output Summary

```yaml
paper_sessions_health:
  total_sessions: 16
  success: 12
  failed: 4
  aborted: 0
  running: 0
  latest_session_id: 20260620_073810_paper_7075f45
  latest_session_state: failed
  latest_issue_id: 20260620_073810_paper_7075f45
  latest_issue_state: failed
  latest_issue_error: DataError
  active_sessions: []
```

## Alerts Output Summary

```yaml
paper_sessions_alerts:
  alert_status: critical
  alert_counts:
    critical: 4
  latest_alert_code: PAPER_SESSION_FAILED
  latest_alert_session_id: 20260620_073810_paper_7075f45
  current_window_alert_status: critical
  current_window_alert_counts:
    critical: 1
  current_window_latest_alert_code: PAPER_SESSION_FAILED
  current_window_latest_alert_session_id: 20260620_073810_paper_7075f45
  stale_after_minutes: 60
  running_sessions: []
```

Interpretation:

- The current operational window correctly reports this failed session as a
  critical paper-session alert.
- No stale or false-stale condition was observed.
- #722 is not indicated by this attempt.

## Protocol Checklist Result

```yaml
protocol_check:
  exactly_one_session_attempted: true
  supervised: true
  paper_only: true
  broker_submit: false
  live_capital: false
  stage_e: blocked
  retry_performed: false
  second_session_started: false
  health_output_captured: true
  alerts_output_captured: true
  operator_note_present: true
```

Required artifact checklist:

```yaml
required_artifacts:
  session_status: present
  report: missing
  metrics: missing
  trades_csv: missing
  health_output: present
  alerts_output: present
  operator_note: present
```

## Failure Classification

```yaml
failure_class:
  type: insufficient_history_after_indicators
  cause: "The selected 7-day window was too short for the configured indicator lookbacks."
  operational_failure: false
  data_window_failure: true
  runtime_crash: false
  broker_related: false
```

This is not a broker, Hyperliquid, Stage E, or signed-action problem. It is a
paper-run input-window problem that surfaced correctly as a terminal failed
paper session.

## Decision

```yaml
decision:
  do_not_mark_paper_live_ready: true
  do_not_retry_in_same_issue: true
  do_not_implement_722_from_this_attempt: true
  next_allowed_work:
    - document failure
    - define corrected preflight/window requirement
    - only then consider a second supervised paper-live session
```

The first supervised paper-live attempt failed, but the protocol was respected.
The next paper-live attempt should only be opened after the required historical
window/preflight requirement is defined so the operator does not repeat a known
insufficient-history setup.
