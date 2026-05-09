# Paper Evidence Review — Failure and Stale Alert Fixture

Issue: [#668](https://github.com/Whiteks1/quantlab/issues/668)

## Metadata

```yaml
date: 2026-05-09
mode: paper_alert_fixture
operator: marce
source_issue: 668
fixture_root: "%TEMP%\\quantlab-paper-alert-fixture"
purpose: "Validate paper failure and stale alert classification without modifying real paper sessions."
```

## Safety Boundary

This validation used a temporary fixture outside the repository:

```text
C:\Users\marce\AppData\Local\Temp\quantlab-paper-alert-fixture
```

No real `outputs/paper_sessions` session was modified.

## Fixture Shape

Two temporary paper session directories were created:

```text
paper_failed_fixture/
  session_status.json
paper_stale_fixture/
  session_status.json
```

Failed fixture:

```json
{
  "session_id": "paper_failed_fixture",
  "status": "failed",
  "status_reason": "exception",
  "terminal": true,
  "started_at": "2026-05-09T20:00:00",
  "updated_at": "2026-05-09T20:01:00",
  "finished_at": "2026-05-09T20:01:00",
  "error_type": "RuntimeError",
  "message": "controlled fixture failure"
}
```

Stale fixture:

```json
{
  "session_id": "paper_stale_fixture",
  "status": "running",
  "status_reason": "active",
  "terminal": false,
  "started_at": "2026-05-09T18:00:00",
  "updated_at": "2026-05-09T18:00:00"
}
```

## Commands

```powershell
.\.venv\Scripts\python.exe main.py --paper-sessions-health $root
.\.venv\Scripts\python.exe main.py --paper-sessions-alerts $root --paper-stale-minutes 60
```

## Health Output

```text
Paper session health: C:\Users\marce\AppData\Local\Temp\quantlab-paper-alert-fixture

  total_sessions      : 2
  success             : 0
  failed              : 1
  aborted             : 0
  running             : 1
  latest_session_id   : paper_failed_fixture
  latest_session_at   : 2026-05-09T20:01:00
  latest_session_state: failed
  latest_issue_id     : paper_failed_fixture
  latest_issue_state  : failed
  latest_issue_at     : 2026-05-09T20:01:00
  latest_issue_error  : RuntimeError
  active_sessions     : ['paper_stale_fixture']
```

## Alerts Output

```json
{
  "alert_counts": {
    "critical": 1,
    "warning": 1
  },
  "alert_status": "critical",
  "alerts": [
    {
      "activity_at": "2026-05-09T20:01:00",
      "age_minutes": 144,
      "alert_code": "PAPER_SESSION_FAILED",
      "error_type": "RuntimeError",
      "message": "controlled fixture failure",
      "path": "C:\\Users\\marce\\AppData\\Local\\Temp\\quantlab-paper-alert-fixture\\paper_failed_fixture",
      "session_id": "paper_failed_fixture",
      "severity": "critical",
      "status": "failed"
    },
    {
      "activity_at": "2026-05-09T18:00:00",
      "age_minutes": 265,
      "alert_code": "PAPER_SESSION_STALE",
      "error_type": null,
      "message": "Paper session has been running for 265 minute(s), exceeding stale threshold of 60 minute(s).",
      "path": "C:\\Users\\marce\\AppData\\Local\\Temp\\quantlab-paper-alert-fixture\\paper_stale_fixture",
      "session_id": "paper_stale_fixture",
      "severity": "warning",
      "status": "running"
    }
  ],
  "generated_at": "2026-05-09T22:25:17",
  "has_alerts": true,
  "latest_alert_code": "PAPER_SESSION_FAILED",
  "running_sessions": [
    "paper_stale_fixture"
  ],
  "stale_after_minutes": 60,
  "status_counts": {
    "failed": 1,
    "running": 1
  },
  "total_sessions": 2
}
```

## Result

```yaml
failed_session_detected: true
failed_session_alert: PAPER_SESSION_FAILED
failed_session_severity: critical
stale_session_detected: true
stale_session_alert: PAPER_SESSION_STALE
stale_session_severity: warning
real_sessions_modified: false
runtime_code_changed: false
```

## Operator Interpretation

The paper alert path can distinguish a terminal failed session from a stale running session using only `session_status.json` fixtures.

This validates operator detection behavior, not paper engine failure recovery.

## Stop / Continue Rule

If a real paper session emits `PAPER_SESSION_FAILED`, stop and inspect `session_status.json` before rerunning.

If a real paper session emits `PAPER_SESSION_STALE`, confirm whether the process is still active before starting another paper session.

## Boundary

- No real paper session was mutated.
- No broker submit occurred.
- No live execution occurred.
- No Stage E scope opened.
- No Stepbit work occurred.
