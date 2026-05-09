# Paper Evidence Review — Second Controlled Paper Session

Issue: [#667](https://github.com/Whiteks1/quantlab/issues/667)

## Metadata

```yaml
date: 2026-05-09
session_id: 20260509_202325_paper_ddc7c3f
mode: paper
operator: marce
source_issue: 667
purpose: "Prove that the paper success path can be repeated with canonical artifacts."
```

## Command

```powershell
.\.venv\Scripts\python.exe main.py --ticker ETH-USD --start 2023-07-01 --end 2024-01-01 --paper --report --initial_cash 10000
```

## Session Path

```text
outputs/paper_sessions/20260509_202325_paper_ddc7c3f
```

## Artifacts Reviewed

- `outputs/paper_sessions/20260509_202325_paper_ddc7c3f/session_status.json`
- `outputs/paper_sessions/20260509_202325_paper_ddc7c3f/report.json`
- `outputs/paper_sessions/20260509_202325_paper_ddc7c3f/metrics.json`
- `outputs/paper_sessions/20260509_202325_paper_ddc7c3f/trades.csv`
- `outputs/paper_sessions/20260509_202325_paper_ddc7c3f/run_report.md`
- `outputs/paper_sessions/20260509_202325_paper_ddc7c3f/artifacts/equity.png`

## Terminal Status

```json
{
  "command": "paper",
  "duration_seconds": 0.951854,
  "finished_at": "2026-05-09T22:23:26.412517",
  "mode": "paper",
  "request_id": null,
  "session_id": "20260509_202325_paper_ddc7c3f",
  "started_at": "2026-05-09T22:23:25.460663",
  "status": "success",
  "status_reason": "completed",
  "terminal": true,
  "updated_at": "2026-05-09T22:23:26.412517"
}
```

## Machine Contract Review

`report.json.machine_contract` exists and identifies the artifact as a paper result.

```json
{
  "schema_version": "1.0",
  "contract_type": "quantlab.paper.result",
  "command": "paper",
  "status": "success",
  "request_id": null,
  "run_id": "20260509_202325_paper_ddc7c3f",
  "mode": "paper",
  "summary": {
    "max_drawdown": -0.023625274044252298,
    "sharpe_simple": 2.6292727151416275,
    "total_return": 0.11764632833778887,
    "trades": 4,
    "win_rate": 0.5
  },
  "artifacts": {
    "metadata": "session_metadata.json",
    "status": "session_status.json",
    "config": "config.json",
    "metrics": "metrics.json",
    "report": "report.json",
    "trades": "trades.csv"
  }
}
```

## Health Output

```text
Paper session health: outputs\paper_sessions

  total_sessions      : 2
  success             : 2
  failed              : 0
  aborted             : 0
  running             : 0
  latest_session_id   : 20260509_202325_paper_ddc7c3f
  latest_session_at   : 2026-05-09T22:23:26.412517
  latest_session_state: success
  latest_issue_id     : None
  latest_issue_state  : None
  latest_issue_at     : None
  latest_issue_error  : None
  active_sessions     : []
```

## Alerts Output

```json
{
  "alert_counts": {},
  "alert_status": "ok",
  "alerts": [],
  "generated_at": "2026-05-09T22:23:38",
  "has_alerts": false,
  "latest_alert_at": null,
  "latest_alert_code": null,
  "latest_alert_session_id": null,
  "latest_success_at": "2026-05-09T22:23:26.412517",
  "latest_success_session_id": "20260509_202325_paper_ddc7c3f",
  "root_dir": "outputs\\paper_sessions",
  "running_sessions": [],
  "stale_after_minutes": 60,
  "status_counts": {
    "success": 2
  },
  "total_sessions": 2
}
```

## Result

```yaml
terminal: true
status: success
machine_contract_present: true
operator_can_diagnose: true
raw_outputs_committed: false
```

## Operator Interpretation

The paper success path is repeatable for this controlled scenario. The second session produced the expected canonical session status, report, machine contract, trades file, run report, and equity artifact.

This does not prove failure handling, stale detection, restart/resume behavior, or broker readiness.

## Stop / Continue Rule

Continue to the failure/stale evidence slice only. Do not promote to broker submit, live execution, Stage E, or automation based on this second success.

## Restart / Resume Expectation

```yaml
proven: false
status: not_tested
note: "This slice proves repeated terminal success, not resume or restart behavior."
```

## Boundary

- No broker submit occurred.
- No live execution occurred.
- No Stage E scope opened.
- No Stepbit work occurred.
- No raw `outputs/` artifacts were committed.
