# Paper-Live Minimum Window Preflight

Issue: [#818](https://github.com/leticia-padilla-dev/quantlab/issues/818)

Status: docs-only preflight rule. No paper session executed by this document.

## Objective

Define the minimum data-window preflight required before attempting a second
supervised paper-live session.

This document exists because session 01 failed before producing a complete
paper result:

```yaml
paper_live_session_01:
  issue: 816
  pr: 817
  session_id: 20260620_073810_paper_7075f45
  status: failed
  error_type: DataError
  message: "No data remaining after applying indicators (need more history for lookbacks)."
  cause: insufficient_history_after_indicators
  retry_performed: false
```

## Boundary

```yaml
boundary:
  docs_only: true
  second_paper_session_authorized: false
  broker_submit: false
  live_capital: false
  stage_e: blocked
  automation: false
  stepbit: false
  runtime_changes: false
```

This preflight does not open Stage E and does not authorize session 02. It only
defines the minimum requirement that must be satisfied before a separate session
02 issue can launch.

## Problem

The first supervised paper-live attempt used a 7-day calendar window:

```yaml
session_01_window:
  ticker: ETH-USD
  start: "2026-06-10"
  end: "2026-06-17"
  interval: 1d
```

That window was too short for the configured indicator stack. After indicator
lookbacks were applied, no usable rows remained.

Operational conclusion:

```yaml
conclusion:
  seven_calendar_days: insufficient
  failure_mode: deterministic_preflight_miss
  next_attempt_requires_window_preflight: true
```

## Minimum Window Rule

For supervised paper-live session 02, use a conservative minimum window:

```yaml
minimum_window_rule:
  interval: 1d
  minimum_calendar_days: 120
  recommended_calendar_days: 180
  minimum_rows_before_indicators: 90
  minimum_rows_after_indicators: 30
```

Rationale:

- The configured strategy uses indicator lookbacks that can consume a meaningful
  portion of the early window.
- Calendar days do not equal data rows.
- A narrow operational drill still needs enough history to survive indicator
  warmup.
- The target is operational validation, not profitability optimization.

If a different interval is selected, the operator must define an equivalent
minimum before launch. Do not infer that 7 calendar days is acceptable for
intraday or daily data.

## Required Preflight Before Session 02

Before launching any second supervised paper-live session, the operator must
write down:

```yaml
preflight_inputs:
  ticker: ""
  start: ""
  end: ""
  interval: ""
  calendar_days: ""
  expected_minimum_rows_before_indicators: ""
  expected_minimum_rows_after_indicators: ""
  command_planned: ""
```

The planned window passes preflight only if:

```yaml
pass_if:
  calendar_days_gte: 120
  expected_rows_before_indicators_gte: 90
  expected_rows_after_indicators_gte: 30
  operator_confirms_window_is_not_a_repeat_of_session_01: true
```

The planned window fails preflight if:

```yaml
stop_if:
  calendar_days_lt: 120
  expected_rows_before_indicators_lt: 90
  expected_rows_after_indicators_lt: 30
  operator_cannot_explain_indicator_warmup_risk: true
```

## How To Check Before Run

Docs-only acceptable check:

1. Count calendar days between `start` and `end`.
2. Confirm the interval is `1d` unless explicitly documented otherwise.
3. Assume non-trading/data gaps may reduce available rows.
4. Apply the conservative rule above.
5. If uncertain, do not launch.

Runtime/data check, if added later, must be a separate issue. This issue does
not implement it.

## Operator Message When Blocked

Use this exact interpretation when the preflight fails:

```text
Paper-live session blocked: the proposed data window is too short to survive
indicator warmup. Do not launch a second session. Define a wider window or add a
separate preflight check before retrying.
```

## Session 02 Planning Template

Use this template in the future session 02 issue:

```yaml
paper_live_session_02_preflight:
  references:
    protocol: docs/ops/supervised-paper-live-session-protocol.md
    session_01_evidence: docs/ops/paper-evidence/paper-live-session-01-failed.md
    minimum_window_preflight: docs/ops/paper-live-minimum-window-preflight.md
  planned_command: ""
  ticker: ""
  start: ""
  end: ""
  interval: ""
  calendar_days: ""
  expected_rows_before_indicators: ""
  expected_rows_after_indicators: ""
  preflight_result: pass|fail
  operator_acknowledges:
    - "This is one paper-only session."
    - "No broker submit is authorized."
    - "No live capital is used."
    - "Stage E remains blocked."
    - "No retry will be performed inside the same issue."
```

## Decision Rule

```yaml
decision:
  session_02_allowed_from_this_issue: false
  next_allowed_work:
    - open a separate session_02 issue
    - include the preflight template
    - launch exactly one paper session only if preflight passes
  not_allowed:
    - launch session_02 from this issue
    - implement runtime checks in this docs slice
    - implement #722 without false-stale evidence
```

## Related Documents

- [supervised-paper-live-session-protocol.md](./supervised-paper-live-session-protocol.md)
- [paper-live-session-01-failed.md](./paper-evidence/paper-live-session-01-failed.md)
- [paper-restart-resume-posture.md](./paper-restart-resume-posture.md)
