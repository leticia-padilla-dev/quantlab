# Paper: Session Terminality Contract

Issue: [#757](https://github.com/Whiteks1/quantlab/issues/757)

Status: docs-only. No runtime changes. No submit. Stage E remains blocked.

## Purpose

Paper operations require a deterministic answer to:

- Is the session terminal?
- If terminal, what terminal category applies?
- If non-terminal, what is the required operator action?

This contract defines terminal vs non-terminal states as a first-class primitive for paper sessions.

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Authoritative Inputs

Terminality must be derived from:

- `outputs/paper_sessions/<session_id>/session_status.json`

Supporting context may be derived from:

- `session_metadata.json`
- `report.json`
- `trades.csv`

Terminality must not require console logs or operator memory.

## Terminality Definitions

```yaml
terminality:
  terminal:
    description: "No further runtime activity is expected for the session id. Evidence capture may proceed."
  non_terminal:
    description: "Further activity might still occur, or the state is ambiguous. Operator must stop and not infer outcomes."
```

## Terminal Categories

```yaml
terminal_categories:
  completed:
    condition: "session_status.terminal == true and session_status.status == success"
    operator_action: "continue_evidence_capture"
  failed:
    condition: "session_status.terminal == true and session_status.status == failed"
    operator_action: "stop"
  aborted:
    condition: "session_status.terminal == true and session_status.status == aborted"
    operator_action: "stop"
  rejected:
    condition: "Explicit operator stop decision recorded; used for governance drills where submit is forbidden."
    operator_action: "stop"
```

Note:
- `rejected` is reserved for governance-controlled drills where a run is intentionally terminated by policy (not by a broker).

## Non-Terminal Categories (Stop-on-Ambiguity)

```yaml
non_terminal_categories:
  running:
    condition: "session_status.terminal == false and session_status.status indicates active execution"
    operator_action: "stop"
  stale:
    condition: "session_status.terminal == false and session exceeds stale threshold"
    operator_action: "stop_and_escalate"
  ambiguous:
    condition: "status is unknown, fields missing, or artifacts inconsistent"
    operator_action: "stop"
```

## Consistency Gates

If any of these are true, treat the session as non-terminal (ambiguous) regardless of `terminal` flag:

```yaml
consistency_gates:
  - "session_status.terminal == true but report.json missing"
  - "session_status.terminal == true but session_metadata.json missing"
  - "session_status.status == success but trades.csv missing"
  - "session_status.status in [failed, aborted] but error fields are missing and message is not actionable"
```

## Deterministic Output Template

```yaml
paper_session_terminality:
  session_id: "<paper_session_id>"
  terminality: terminal
  category: completed
  severity: ok
  operator_action: continue_evidence_capture
  evidence:
    status_artifact: "outputs/paper_sessions/<session_id>/session_status.json"
    report_artifact: "outputs/paper_sessions/<session_id>/report.json"
```

## Non-Goals

- This contract does not authorize broker actions.
- This contract does not authorize submit retries.
- This contract does not open Stage E.
