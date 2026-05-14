# Paper: Deterministic Operator Interpretation Contract

Issue: [#756](https://github.com/Whiteks1/quantlab/issues/756)

Status: docs-only. No runtime changes. No submit. Stage E remains blocked.

## Purpose

Given the same paper session artifacts, two operators should reach the same conclusions.

This contract defines:

- required inputs (which artifacts/fields are authoritative)
- deterministic outputs (terminality, severity, and next action)
- stop rules for ambiguity

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Inputs (Authoritative Sources)

Paper sessions are authoritative only through their canonical artifact pack:

- `outputs/paper_sessions/<session_id>/session_status.json`
- `outputs/paper_sessions/<session_id>/session_metadata.json`
- `outputs/paper_sessions/<session_id>/report.json`
- `outputs/paper_sessions/<session_id>/trades.csv`

When present, these are supporting evidence (not replacements for status):

- `config.json`
- `metrics.json`
- `run_report.md`

Non-authoritative sources (must not be required for conclusions):

- console logs
- screenshots
- operator memory

## Deterministic Outputs

```yaml
operator_conclusion:
  terminality: terminal | non_terminal
  severity: ok | warning | critical
  next_action:
    - continue_evidence_capture
    - stop
    - escalate
  rationale:
    required_fields: []
    notes: ""
```

## Decision Procedure (Minimal)

### Step 0 — Artifact presence gate

If `session_status.json` is missing or not parseable:

- terminality: non_terminal
- severity: critical
- next_action: stop

### Step 1 — Session terminality gate

Read from `session_status.json`:

- `terminal` (boolean)
- `status` (string)
- `status_reason` (string)
- `error_type` (optional)
- `message` (optional)

Decision:

```yaml
terminality_rules:
  - if: "terminal == false"
    then: { terminality: non_terminal, severity: warning, next_action: stop }
  - if: "terminal == true and status == success"
    then: { terminality: terminal, severity: ok, next_action: continue_evidence_capture }
  - if: "terminal == true and status in [failed, aborted]"
    then: { terminality: terminal, severity: critical, next_action: stop }
  - if: "terminal == true and status not in [success, failed, aborted]"
    then: { terminality: non_terminal, severity: critical, next_action: stop }
```

### Step 2 — Ambiguity gate (stop-on-ambiguity)

If any of these are true, treat the session as ambiguous and stop:

```yaml
ambiguity_conditions:
  - "terminal == false and updated_at is stale relative to operator expectations"
  - "status == unknown"
  - "error_type present but message missing or not actionable"
  - "report.json missing while session_status reports success"
  - "session_status indicates terminal but required artifacts are missing"
```

Output:

- terminality: non_terminal
- severity: critical
- next_action: stop

### Step 3 — Evidence completeness gate (minimal)

Even when `terminal == true`, the operator must confirm minimum artifacts exist:

```yaml
required_for_minimal_review:
  - session_metadata.json
  - session_status.json
  - report.json
  - trades.csv
```

If any are missing:

- terminality: non_terminal
- severity: critical
- next_action: stop

## Classification Template (copy/paste)

```yaml
operator_conclusion:
  session_id: "<paper_session_id>"
  terminality: terminal
  severity: ok
  next_action: continue_evidence_capture
  rationale:
    required_fields:
      - "session_status.terminal"
      - "session_status.status"
      - "session_status.status_reason"
    notes: ""
```

## Non-Goals

- This contract does not authorize broker actions.
- This contract does not authorize submit retries.
- This contract does not open Stage E.
