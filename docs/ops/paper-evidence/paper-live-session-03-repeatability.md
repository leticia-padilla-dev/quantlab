# Paper-Live Session 03 - Repeatability Evidence

Issue: [#824](https://github.com/leticia-padilla-dev/quantlab/issues/824)

Status: evidence memo. One supervised paper-live repeatability session was
executed. No retry.

## Summary

```yaml
paper_live_session_03:
  session_id: 20260620_082552_paper_3c365d2
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
  classification: second_successful_supervised_paper_live_session
```

This session repeats the supervised paper-live happy path after session 02. It
validates that the paper-live workflow can complete successfully more than once
under the current governance discipline.

It does not authorize broker submit, live capital, Stage E, automation, or
strategy promotion.

## Preflight

```yaml
paper_live_session_03_preflight:
  ticker: ETH-USD
  interval: 1d
  start: "2025-11-01"
  end: "2026-06-17"
  calendar_days: 228
  minimum_calendar_days: 120
  recommended_calendar_days: 180
  expected_rows_before_indicators: ">= 90"
  expected_rows_after_indicators: ">= 30"
  preflight_result: pass
```

References:

- `docs/ops/supervised-paper-live-session-protocol.md`
- `docs/ops/paper-live-minimum-window-preflight.md`
- `docs/ops/paper-live-readiness-reaudit-after-session-02.md`
- `docs/ops/paper-evidence/paper-live-session-02-success.md`

## Command Used

```powershell
.\.venv\Scripts\python.exe main.py --ticker ETH-USD --start 2025-11-01 --end 2026-06-17 --paper --report --initial_cash 10000
```

## Session Path

```text
outputs/paper_sessions/20260620_082552_paper_3c365d2
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
  started_at: "2026-06-20T10:25:52.427549"
  updated_at: "2026-06-20T10:25:53.366044"
  finished_at: "2026-06-20T10:25:53.366044"
  duration_seconds: 0.938495
  report_contract_type: quantlab.paper.result
  report_present: true
```

## Metrics Summary

This is operational repeatability evidence, not profitability validation.

```yaml
metrics:
  status: success
  total_return: -0.13269087655055134
  max_drawdown: -0.2014087973292481
  sharpe_simple: -0.7144535839748035
  trades: 17
  trade_trades: 8
  win_rate: 0.25
  days: 129
```

Interpretation:

- The paper session completed and produced required artifacts.
- Strategy performance was negative.
- Negative performance does not invalidate the operational objective.
- No strategy promotion is implied.

## Trades Evidence

`trades.csv` exists and includes 17 paper broker trade log rows.

The first rows confirm paper broker trade-level evidence was written:

```text
timestamp,side,close,exec_price,qty,fee,equity_after,slippage,reason
2026-02-25,BUY,2054.6279296875,2056.2716320312497,4.853444381830742,20.0,9972.022382094325,0.0008,signal=1
2026-02-27,SELL,1930.7618408203125,1929.2172313476563,0.0,18.72669706563068,9344.62183574971,0.0008,signal=-1
```

## Machine Contract

`report.json` includes the canonical paper machine contract:

```yaml
machine_contract:
  schema_version: "1.0"
  contract_type: quantlab.paper.result
  command: paper
  status: success
  run_id: 20260620_082552_paper_3c365d2
  mode: paper
  artifacts:
    metadata: session_metadata.json
    status: session_status.json
    config: config.json
    metrics: metrics.json
    report: report.json
    trades: trades.csv
```

## Health Output Summary

```yaml
paper_sessions_health:
  total_sessions: 18
  success: 14
  failed: 4
  aborted: 0
  running: 0
  latest_session_id: 20260620_082552_paper_3c365d2
  latest_session_state: success
  latest_issue_id: 20260620_073810_paper_7075f45
  latest_issue_state: failed
  latest_issue_error: DataError
  active_sessions: []
```

Interpretation:

- Session 03 is the latest successful paper session.
- Historical/current issue state still surfaces the session 01 failure.
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
  current_window_latest_success_session_id: 20260620_082552_paper_3c365d2
  current_window_status_counts:
    failed: 1
    success: 2
  running_sessions: []
```

Interpretation:

- Alerts remain critical because session 01 failed and remains inside the
  current alert window.
- This is retained failure evidence, not a session 03 failure.
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

## Repeatability Interpretation

```yaml
repeatability:
  successful_supervised_sessions:
    - 20260620_080032_paper_cca97b7
    - 20260620_082552_paper_3c365d2
  controlled_failures:
    - 20260620_073810_paper_7075f45
  repeatability_evidence_improved: true
  readiness_requires_reaudit: true
```

Session 03 provides the second successful supervised paper-live session. That
is stronger repeatability evidence than session 02 alone, but readiness should
still be decided by a separate re-audit, not by this evidence memo itself.

## Decision

```yaml
decision:
  paper_live_ready: false
  session_03_result: second_successful_supervised_paper_live_session
  do_not_implement_722_from_this_session: true
  do_not_promote_strategy: true
  next_allowed_work:
    - paper_live_repeatability_reaudit
    - decide whether paper-live operational readiness can be marked conditionally ready
```

The third supervised paper-live attempt successfully repeated the happy path
under the current minimum-window preflight and protocol boundaries. It should
feed a repeatability re-audit, not an automatic promotion.
