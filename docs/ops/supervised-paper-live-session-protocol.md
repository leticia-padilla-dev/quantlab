# Supervised Paper-Live Session Protocol

Issue: [#814](https://github.com/leticia-padilla-dev/quantlab/issues/814)

Status: protocol only. No paper session executed by this document.

## Objective

Define the operator protocol for the first supervised paper-live session.

The purpose is to prove that QuantLab can run a paper session as an
operationally supervised workflow with explicit boundaries, artifacts, health
checks, alert review, and stop conditions.

This protocol is not a broker, live-capital, Stage E, or automation
authorization.

## Boundary

```yaml
boundary:
  mode: paper_live_supervised
  broker_submit: false
  live_capital: false
  hyperliquid_submit: false
  retry: false
  close: false
  stage_e: blocked
  automation: false
  stepbit: false
  desktop_submit_authority: false
```

Paper-live means:

- the operator treats the paper session as a live operational drill
- the session is supervised and reviewed through artifacts
- no broker or exchange mutation is allowed

Paper-live does not mean:

- live trading
- broker-connected execution
- Stage E
- automatic promotion
- unattended automation

## Preconditions

Before the first supervised paper-live session:

```yaml
preconditions:
  d3_posture:
    stage_e: blocked
    issue_800: closed_no_go_terminal
    issue_812: closed_after_postmortem_review
  signed_action_integrity:
    issue_810: merged
    issue_812_postmortem_reviewed: true
    unresolved_signed_action_roundtrip_blocker: false
  paper_governance:
    paper_session_runbook_reviewed: docs/paper-session-runbook.md
    restart_resume_posture_reviewed: docs/ops/paper-restart-resume-posture.md
  operator:
    present: true
    understands_paper_not_broker: true
    understands_restart_means_new_session: true
```

If any precondition is unclear, stop and document the ambiguity before launching
paper.

## Session Definition

The first supervised paper-live session should be intentionally narrow.

```yaml
session_definition:
  asset: "ETH-USD preferred unless operator selects another documented asset"
  mode: paper
  session_count: 1
  duration: "short controlled window first"
  goal: "operational evidence, not profit or strategy promotion"
  expected_output_root: outputs/paper_sessions/<session_id>/
```

Recommended command shape:

```powershell
python main.py --ticker ETH-USD --start <start> --end <end> --paper --report --initial_cash 10000
```

The exact command must be recorded in the evidence memo before the session is
interpreted.

## Required Artifacts

The session is not reviewable unless these artifacts exist:

```yaml
required_artifacts:
  session_directory: outputs/paper_sessions/<session_id>/
  files:
    - session_metadata.json
    - session_status.json
    - config.json
    - metrics.json
    - report.json
    - run_report.md
    - trades.csv
```

Required post-session command outputs:

```yaml
required_review_outputs:
  - "python main.py --paper-sessions-list outputs/paper_sessions"
  - "python main.py --paper-sessions-show outputs/paper_sessions/<session_id>"
  - "python main.py --paper-sessions-health outputs/paper_sessions"
  - "python main.py --paper-sessions-alerts outputs/paper_sessions --paper-stale-minutes 60 --paper-alert-window-days 7 --paper-alert-window-sessions 20"
```

If any required artifact is missing, classify the session as incomplete and do
not promote it into readiness evidence.

## Before Session Checklist

```yaml
before_session:
  - confirm Stage E remains blocked
  - confirm this is paper-only
  - confirm no broker submit path is invoked
  - record intended asset, command, start/end window, and initial cash
  - confirm expected output root is outputs/paper_sessions/
  - confirm restart means new session id
  - confirm stale is a stop-and-classify condition
```

## During Session Checklist

```yaml
during_session:
  - keep operator present
  - do not interrupt unless stop condition triggers
  - do not start a second session while the first is unresolved
  - if process appears stuck, inspect status before rerun
  - if interrupted, classify as aborted/stale before any restart
```

## After Session Checklist

```yaml
after_session:
  - identify session_id
  - inspect session_status.json
  - run paper session list/show/health/alerts commands
  - verify required artifacts exist
  - inspect report.json and trades.csv
  - record terminal status
  - record health status
  - record alert status
  - record operator interpretation
```

## Stop Conditions

Stop immediately and document if:

```yaml
stop_if:
  - session_status.json missing
  - session remains running beyond expected duration
  - health reports failed/aborted/stale state
  - alerts report PAPER_SESSION_FAILED
  - alerts report PAPER_SESSION_ABORTED
  - alerts report PAPER_SESSION_STALE
  - artifacts are incomplete
  - operator cannot explain the current session state from artifacts
  - any broker/live submit path appears in the workflow
```

Stop means:

- do not start a second session immediately
- classify the current session first
- write an evidence memo
- only restart as a new session id after classification

## Stale And #722 Decision Rule

#722 is not required before the first supervised paper-live session.

Implement #722 only if a real supervised paper-live session demonstrates:

```yaml
implement_722_if:
  paper_session_actually_running: true
  session_known_alive_by_operator: true
  session_status_updated_at_not_refreshing: true
  alerts_classify_stale_incorrectly: true
```

If no false-stale behavior appears, keep #722 open but deferred.

## Restart / Resume Rule

QuantLab currently uses the documented restart-only posture:

```yaml
restart_resume:
  resume_supported: false
  restart_policy: "new session id"
  evidence_mixing_allowed: false
```

Reference:

- [paper-restart-resume-posture.md](./paper-restart-resume-posture.md)

After interruption:

1. identify the prior `session_id`
2. inspect `session_status.json`
3. classify completed / aborted / stale / failed
4. write the classification in the evidence memo
5. restart only as a new session id if needed

## Evidence Memo Requirements

After the first supervised paper-live session, create a separate evidence memo
under `docs/ops/paper-evidence/`.

Minimum memo shape:

```yaml
paper_live_evidence:
  session_id: ""
  command_used: ""
  session_path: outputs/paper_sessions/<session_id>
  terminal_status: ""
  health_status: ""
  alert_status: ""
  required_artifacts_present: true
  trades_count: ""
  report_json_reviewed: true
  trades_csv_reviewed: true
  stale_observed: false
  false_stale_observed: false
  operator_interpretation: ""
  next_decision:
    - continue_paper_live_evidence
    - implement_722_if_false_stale
    - re_audit
```

The memo must explicitly state:

- no broker submit occurred
- no live capital was used
- no Stage E opening occurred
- no automation was enabled

## Re-Audit Inputs

The next readiness re-audit may use the first supervised paper-live session only
if:

```yaml
reaudit_inputs:
  - evidence memo exists
  - required artifacts exist
  - health output captured
  - alerts output captured
  - terminal status is understood
  - stale/failure posture is documented
  - operator can explain the session from artifacts
```

If those are not satisfied, the result is not readiness evidence.

## Related Documents

- [paper-session-runbook.md](../paper-session-runbook.md)
- [paper-restart-resume-posture.md](./paper-restart-resume-posture.md)
- [d3-issue-812-rejected-submit-postmortem.md](./d3-issue-812-rejected-submit-postmortem.md)
- [d3-operator-hardening-declarations.md](./d3-operator-hardening-declarations.md)
