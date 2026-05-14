# Paper 2026-05-14 — Alert Posture Interpretation Drill (Operational Evidence Memo)

Issue: [#782](https://github.com/Whiteks1/quantlab/issues/782)

artifact_type: operational_evidence_memo

## Scope / Constraints

```yaml
scope:
  objective: validate_operator_interpretation_of_alert_posture
  paper_only: true
  broker_actions: false
  submit_allowed: false
  stage_e: blocked
  retry_allowed: false
  auto_adjust: false
  auto_resubmit: false
```

## Drill Objective

Demonstrate that an operator can deterministically interpret:

- historical posture (`alert_status` / `alerts[]`)
- current operational window posture (`current_window_*`)

using explicit horizon flags, without hiding or rewriting historical failures.

## Commands Executed

```bash
python main.py --paper-sessions-health outputs/paper_sessions
python main.py --paper-sessions-alerts outputs/paper_sessions --paper-stale-minutes 60 --paper-alert-window-days 7 --paper-alert-window-sessions 20
python main.py --paper-sessions-alerts outputs/paper_sessions --paper-stale-minutes 60 --paper-alert-window-days 1 --paper-alert-window-sessions 5
```

## Artifacts (Local, Not Versioned)

These drill outputs were written under:

```yaml
drill_outputs:
  root_dir: outputs/ops_drills/paper_alert_posture_782_20260514_143616
  files:
    paper_sessions_health_txt: outputs/ops_drills/paper_alert_posture_782_20260514_143616/paper_sessions_health.txt
    alerts_horizon_7d_20s_json: outputs/ops_drills/paper_alert_posture_782_20260514_143616/paper_sessions_alerts_horizon_7d_20s.json
    alerts_horizon_1d_5s_json: outputs/ops_drills/paper_alert_posture_782_20260514_143616/paper_sessions_alerts_horizon_1d_5s.json
```

## Observed Results (Posture Snapshots)

### Horizon: 7 days AND 20 sessions

```yaml
snapshot:
  generated_at: "2026-05-14T14:55:00"
  horizon:
    mode: and
    window_days: 7
    window_sessions: 20
  historical:
    alert_status: critical
    alert_counts:
      critical: 3
  current_window:
    alert_status: critical
    alert_counts:
      critical: 3
    latest_alert:
      session_id: 20260514_103624_paper_4f358ba
      code: PAPER_SESSION_FAILED
      at: "2026-05-14T12:36:25"
```

### Horizon: 1 day AND 5 sessions

```yaml
snapshot:
  generated_at: "2026-05-14T14:55:01"
  horizon:
    mode: and
    window_days: 1
    window_sessions: 5
  historical:
    alert_status: critical
    alert_counts:
      critical: 3
  current_window:
    alert_status: critical
    alert_counts:
      critical: 2
    latest_alert:
      session_id: 20260514_103624_paper_4f358ba
      code: PAPER_SESSION_FAILED
      at: "2026-05-14T12:36:25"
```

## Interpretation (Per Operator Rules)

Interpretation source:

- `docs/ops/paper-alert-posture-interpretation-rules.md`

```yaml
operator_conclusion:
  current_window_posture: critical
  next_action: stop
  rationale:
    - "current_window_alert_status is critical in both horizons"
    - "horizon tightening changes counts but does not hide recent failures"
```

## Notes

- This drill validates the operator model: horizon affects only the current window slice; historical visibility remains present and explicit.
- This drill does not authorize any broker actions or Stage E work.
