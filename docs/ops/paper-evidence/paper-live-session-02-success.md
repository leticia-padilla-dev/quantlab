# Paper-Live Session 02 - Successful Supervised Attempt

Issue: [#820](https://github.com/leticia-padilla-dev/quantlab/issues/820)

Status: evidence memo. One supervised paper-live attempt was executed. No retry.

## Summary

```yaml
paper_live_session_02:
  session_id: 20260620_080032_paper_cca97b7
  result: success
  terminal_status: success
  status_reason: completed
  retry_performed: false
  second_session_started: false
  broker_submit: false
  live_capital: false
  stage_e: blocked
  automation: false
  paper_live_ready: false
  classification: first_successful_supervised_paper_live_session
```

This session validates the happy path once after applying the minimum window
preflight from #818. It does not establish repeatable paper-live readiness by
itself.

## Preflight

```yaml
paper_live_session_02_preflight:
  ticker: ETH-USD
  interval: 1d
  start: "2025-12-01"
  end: "2026-06-17"
  calendar_days: 198
  minimum_calendar_days: 120
  recommended_calendar_days: 180
  expected_rows_before_indicators: ">= 90"
  expected_rows_after_indicators: ">= 30"
  preflight_result: pass
```

References:

- `docs/ops/supervised-paper-live-session-protocol.md`
- `docs/ops/paper-live-minimum-window-preflight.md`
- `docs/ops/paper-evidence/paper-live-session-01-failed.md`

## Command Used

```powershell
.\.venv\Scripts\python.exe main.py --ticker ETH-USD --start 2025-12-01 --end 2026-06-17 --paper --report --initial_cash 10000
```

## Session Path

```text
outputs/paper_sessions/20260620_080032_paper_cca97b7
```

## Artifact Inventory

Present:

```yaml
present_artifacts:
  - artifacts/
  - config.json
  - metadata.json
  - metrics.json
  - report.json
  - run_report.md
  - session_metadata.json
  - session_status.json
  - trades.csv
```

Missing:

```yaml
missing_artifacts: []
```

## Session Status

```yaml
session_status:
  command: paper
  mode: paper
  status: success
  status_reason: completed
  terminal: true
  started_at: "2026-06-20T10:00:32.243811"
  updated_at: "2026-06-20T10:00:33.052978"
  finished_at: "2026-06-20T10:00:33.052978"
  duration_seconds: 0.809167
```

## Metrics Summary

This is operational evidence, not profitability validation.

```yaml
metrics:
  status: success
  total_return: -0.07257336883906462
  max_drawdown: -0.10957646652877129
  sharpe_simple: -0.594896193925529
  trades: 11
  trade_trades: 5
  win_rate: 0.2
  days: 99
```

Interpretation:

- The paper session completed and produced the required artifacts.
- Strategy performance was negative.
- Negative performance does not invalidate the operational objective of this
  slice.
- No strategy promotion is implied.

## Trades Evidence

`trades.csv` exists and includes 11 paper broker trade log rows.

The first rows confirm the paper broker wrote trade-level execution evidence:

```text
timestamp,side,close,exec_price,qty,fee,equity_after,slippage,reason
2026-03-23,BUY,2152.14599609375,2153.8677128906247,4.633525049041298,20.0,9972.022382094327,0.0008,signal=1
2026-03-26,SELL,2059.578369140625,2057.9307064453124,0.0,19.070946955011216,9516.402530550597,0.0008,signal=-1
```

## Health Output Summary

```yaml
paper_sessions_health:
  total_sessions: 17
  success: 13
  failed: 4
  aborted: 0
  running: 0
  latest_session_id: 20260620_080032_paper_cca97b7
  latest_session_state: success
  latest_issue_id: 20260620_073810_paper_7075f45
  latest_issue_state: failed
  latest_issue_error: DataError
  active_sessions: []
```

Interpretation:

- The latest session is successful.
- Historical/current issue state still surfaces session 01 failure, as expected.
- No active/running sessions remain.

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
  current_window_latest_success_session_id: 20260620_080032_paper_cca97b7
  current_window_status_counts:
    failed: 1
    success: 1
  running_sessions: []
```

Interpretation:

- Alerts remain critical because session 01 failed and remains within the
  current operational window.
- This is correct alert-retention behavior, not a session 02 failure.
- No stale or false-stale condition was observed.
- #722 is not indicated by this session.

## Protocol Checklist Result

```yaml
protocol_check:
  preflight_recorded: true
  exactly_one_session_attempted: true
  supervised: true
  paper_only: true
  broker_submit: false
  live_capital: false
  stage_e: blocked
  retry_performed: false
  second_session_started: false
  session_status: present
  report: present
  metrics: present
  trades_csv: present
  health_output: present
  alerts_output: present
  operator_note: present
```

## Decision

```yaml
decision:
  paper_live_ready: false
  session_02_result: first_successful_supervised_paper_live_session
  do_not_implement_722_from_this_session: true
  do_not_promote_strategy: true
  next_allowed_work:
    - paper_live_readiness_reaudit
    - decide whether another supervised paper-live repeatability session is required
```

The second supervised paper-live attempt successfully validated the happy path
once after applying the minimum window preflight. It should feed a readiness
re-audit, not an automatic promotion.
