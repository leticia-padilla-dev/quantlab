# Supervised Paper-Live Operating Cadence

Issue: [#828](https://github.com/leticia-padilla-dev/quantlab/issues/828)

Status: governance document. No paper session was executed by this document.

## Objective

Define how supervised paper-live should be operated after conditional
paper-only repeatability was validated.

The goal is to move from isolated drills to a consistent operational practice
without expanding authority into broker submit, live capital, Stage E,
automation, Stepbit, or runtime changes.

## Boundary

```yaml
boundary:
  mode: supervised_paper_live
  status: governed_conditional_paper_only_operation
  broker_submit: false
  live_capital: false
  stage_e: blocked
  automation: false
  stepbit: false
  runtime_changes: false
  heartbeat_722_implemented: false
```

Paper-live remains a supervised paper-only operational drill. It is not live
trading, broker readiness, Stage E, or strategy promotion.

## Current Evidence Basis

```yaml
evidence_basis:
  repeatability_reaudit: docs/ops/paper-live-repeatability-reaudit-after-session-03.md
  protocol: docs/ops/supervised-paper-live-session-protocol.md
  preflight: docs/ops/paper-live-minimum-window-preflight.md
  session_01: docs/ops/paper-evidence/paper-live-session-01-failed.md
  session_02: docs/ops/paper-evidence/paper-live-session-02-success.md
  session_03: docs/ops/paper-evidence/paper-live-session-03-repeatability.md
```

The current status is:

```yaml
paper_live:
  repeatability_conditionally_validated: true
  readiness: conditional_paper_only_ready
  scope: supervised_paper_only

still_blocked:
  - broker_submit
  - live_capital
  - Stage_E
  - Stepbit
  - runtime_heartbeat_722_without_false_stale_evidence
```

## Operating Cadence

```yaml
cadence:
  default: manual
  scheduled_default: none
  optional_frequency: weekly_if_operator_approves
  automatic_execution: false
```

Default rule:

- Do not run paper-live on a timer by default.
- Run it manually when there is a clear operational reason.
- A weekly cadence is allowed only if the operator explicitly opens a dedicated
  issue and confirms the evidence requirement for each session.

## Allowed Triggers

Paper-live sessions may be opened only for one of these reasons:

```yaml
allowed_triggers:
  per_research_candidate:
    description: "A research candidate has enough evidence to justify paper-only operational observation."
    requires:
      - decision memo or candidate note
      - explicit paper-only boundary
      - minimum-window preflight

  scheduled_manual_review:
    description: "Operator intentionally runs a manual paper-live cadence check."
    requires:
      - dedicated issue
      - stated reason for the check
      - no broker/live implication

  post_config_change_validation:
    description: "A config or operational parameter changed and paper-only behavior needs validation."
    requires:
      - reference to changed config or parameter
      - expected impact
      - one-session limit
```

Forbidden triggers:

```yaml
forbidden_triggers:
  - curiosity_without_issue
  - strategy_promotion_shortcut
  - broker_readiness_claim
  - Stage_E_preparation_without_gate
  - automatic_scheduled_execution_without_operator_issue
```

## Per-Session Rule

Every supervised paper-live session must use:

```yaml
session_rule:
  one_issue: true
  one_branch: true
  exactly_one_session: true
  retry_inside_issue: false
  second_session_if_failure: false
  evidence_memo_required: true
```

If a session fails, the issue produces a failure memo. It does not rerun.

## Required Preflight

Before launch, the operator must apply:

```yaml
preflight:
  required: true
  source: docs/ops/paper-live-minimum-window-preflight.md
  minimum_calendar_days: 120
  recommended_calendar_days: 180
  minimum_rows_before_indicators: 90
  minimum_rows_after_indicators: 30
```

The evidence memo must record:

```yaml
preflight_record:
  ticker: ""
  interval: ""
  start: ""
  end: ""
  calendar_days: ""
  expected_rows_before_indicators: ""
  expected_rows_after_indicators: ""
  preflight_result: pass|fail
```

Do not launch if preflight is ambiguous.

## Required Evidence

Every paper-live evidence memo must include:

```yaml
required_evidence:
  artifacts:
    - session_status.json
    - report.json
    - metrics.json
    - trades.csv
    - run_report.md
  command_outputs:
    - paper_sessions_list
    - paper_sessions_show
    - paper_sessions_health
    - paper_sessions_alerts
  operator_note:
    - terminal_status
    - health_interpretation
    - alert_interpretation
    - stale_observed
    - false_stale_observed
    - broker_submit_false
    - stage_e_blocked
```

Missing required evidence means the session is incomplete for readiness
purposes, even if the underlying command returned success.

## Stop Conditions

Stop and document immediately if any of these occur:

```yaml
stop_conditions:
  - failed_session
  - stale_session
  - missing_session_status
  - missing_report_json
  - missing_metrics_json
  - missing_trades_csv
  - unclear_alert_state
  - operator_cannot_explain_state
  - broker_or_live_path_appears
  - Stage_E_boundary_becomes_ambiguous
```

Stop means:

- do not retry inside the same issue
- do not start a second session
- classify the current session
- write the evidence memo
- open a separate follow-up only after classification

## Pause Conditions

Pause the paper-live cadence if:

```yaml
pause_conditions:
  repeated_failures:
    threshold: "2 consecutive failures or 3 failures in a recent review window"
    action: "stop sessions and open failure-classification issue"

  ambiguous_health_or_alerts:
    action: "stop sessions and document interpretation gap"

  false_stale_observed:
    action: "stop sessions and consider #722 or a replacement heartbeat issue"

  protocol_drift:
    action: "stop sessions and update governance before any more execution"

  evidence_incomplete:
    action: "stop sessions until artifact coverage is restored"
```

Paper-live should not continue by habit after a pause condition.

## Re-Audit Triggers

Open a documentation-only re-audit when:

```yaml
reaudit_triggers:
  after_n_successful_sessions:
    n: 3
    scope: "review whether cadence remains useful and bounded"

  after_failure_class_change:
    description: "A new failure class appears that is not already governed."

  before_any_stage_e_scoping:
    description: "Paper-live evidence must be summarized before any broker/live scoping discussion."

  after_runtime_or_alert_model_change:
    description: "If session status, alerts, heartbeat, or artifact behavior changes."

  after_operator_changes_cadence:
    description: "If manual cadence becomes weekly or otherwise scheduled."
```

Re-audit remains docs-only unless a separate issue explicitly authorizes
runtime work.

## #722 Heartbeat Policy

```yaml
heartbeat_722_policy:
  implement_only_if_false_stale_observed: true
  current_status: deferred
  not_required_by:
    - session_01
    - session_02
    - session_03
```

#722 becomes relevant only if all of these are true:

```yaml
implement_722_if:
  paper_session_actually_running: true
  session_known_alive_by_operator: true
  session_status_updated_at_not_refreshing: true
  alerts_classify_stale_incorrectly: true
```

Do not implement heartbeat because it is theoretically useful. Implement it
only from observed false-stale evidence or a separate explicit runtime
observability requirement.

## Stage E Boundary

```yaml
stage_e:
  status: blocked
  paper_live_cadence_does_not_open_stage_e: true
  broker_submit_authorized: false
  live_capital_authorized: false
```

Before any broker/live discussion, a separate scoping prerequisite issue must
define:

- signed-action integrity references
- D.3 declarations
- stop-control readiness
- reconciliation and alert interpretation
- artifact durability requirements
- no-go conditions

That issue must not activate Stage E.

## Session Issue Template

Use this template when opening a future paper-live session:

```yaml
paper_live_session:
  objective: ""
  trigger:
    type: per_research_candidate|scheduled_manual_review|post_config_change_validation
    reason: ""
  boundary:
    broker_submit: false
    live_capital: false
    stage_e: blocked
    automation: false
    retry: false
  preflight:
    ticker: ""
    interval: ""
    start: ""
    end: ""
    calendar_days: ""
    preflight_result: pass|fail
  acceptance:
    exactly_one_session_attempted: true
    health_output_recorded: true
    alerts_output_recorded: true
    evidence_memo_created: true
```

## Decision

```yaml
decision:
  paper_live_status: governed_conditional_paper_only_operation
  cadence: manual_by_default
  preflight_required: true
  evidence_required: true
  stop_conditions_defined: true
  pause_conditions_defined: true
  reaudit_conditions_defined: true
  stage_e: blocked
  broker_submit: false
  live_capital: false
```

Paper-live is now governed as a conditional paper-only operating practice. It
can continue only through explicit issues, preflight, one-session discipline,
and evidence memos. It must not drift into broker/live execution or unattended
automation.
