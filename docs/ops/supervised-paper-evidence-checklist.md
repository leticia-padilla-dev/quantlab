# Supervised Paper Evidence Checklist

Issue: [#666](https://github.com/Whiteks1/quantlab/issues/666)

Status: required evidence checklist for disciplined supervised paper operation.

Baseline audit:

- [Supervised Paper Operation Readiness Audit](./supervised-paper-readiness-audit.md)

## Purpose

Define the minimum evidence required before QuantLab can claim disciplined supervised paper operation.

This checklist does not authorize broker submit, live execution, Stage E, automation, or Desktop execution controls.

## Readiness Rule

Paper operation is not ready because a single happy-path paper session completed successfully.

It is ready only when QuantLab demonstrates that paper sessions can be launched, reviewed, diagnosed, and stopped or classified under non-happy-path conditions using canonical artifacts and documented operator actions.

## Required Evidence

| Evidence Item | Required | Why It Matters | Accepted Evidence |
|---|---:|---|---|
| Second successful paper session | yes | Proves the success path is repeatable | Session path, `session_status.json`, `report.json.machine_contract` |
| Failed or aborted paper sample | yes | Proves non-success states are visible | Safe fixture, simulated session, or real non-destructive sample |
| Stale detection sample | yes | Proves stuck sessions do not silently look healthy | `--paper-sessions-alerts` output with stale classification |
| Health output captured | yes | Proves operator pulse is reproducible | `--paper-sessions-health outputs/paper_sessions` output |
| Alerts output captured | yes | Proves alert snapshot is machine-readable | `--paper-sessions-alerts outputs/paper_sessions` output |
| `report.json.machine_contract` reviewed | yes | Confirms canonical result surface | Excerpt or explicit review note |
| Operator note | yes | Records human interpretation and next action | Docs memo under `docs/ops/paper-evidence/` |
| Stop condition documented | yes | Prevents ambiguous reruns or silent continuation | Explicit stop rule in evidence memo |
| Restart/resume expectation documented | yes | Separates proven behavior from assumptions | Memo section: proven / not proven / blocked |

## Evidence Memo Template

Use this structure for each paper evidence pass:

````markdown
# Paper Evidence Review — <session_id or scenario>

## Metadata

```yaml
date: YYYY-MM-DD
session_id: ""
mode: paper
operator: ""
source_issue: ""
````

## Command / Setup

```text
<exact command or fixture description>
```

## Artifacts Reviewed

- `outputs/paper_sessions/<session_id>/session_status.json`
- `outputs/paper_sessions/<session_id>/report.json`
- `outputs/paper_sessions/<session_id>/metrics.json`
- `outputs/paper_sessions/<session_id>/trades.csv`

## Health / Alerts

```text
<captured health output>
<captured alerts output>
```

## Result

```yaml
terminal: true|false
status: success|failed|aborted|running|stale
machine_contract_present: true|false
operator_can_diagnose: true|false
```

## Stop / Continue Rule

```text
<explicit operator stop or continue decision>
```

## Restart / Resume Expectation

```text
<proven, not proven, or blocked>
```
```

## Minimum Declaration Before Re-Audit

Before a readiness re-audit can upgrade paper status, the evidence set must show:

- at least two successful paper sessions
- at least one safe non-success or stale detection sample
- health and alerts outputs captured after evidence generation
- no silent success when a session is missing a valid terminal artifact
- operator notes explaining stop/continue decisions

## Explicit Non-Goals

- No broker submit.
- No live execution.
- No autonomous execution.
- No Stage E.
- No Desktop broker controls.
- No Stepbit adapter work.
- No strategy promotion from paper evidence alone.

## Frozen Tracks

```yaml
frozen_until_operational_block_closes:
  - "#61 Stepbit QuantLabTool MVP"
  - Stage_E
  - automation
  - new_venues
  - broker_submit_from_Desktop
```
