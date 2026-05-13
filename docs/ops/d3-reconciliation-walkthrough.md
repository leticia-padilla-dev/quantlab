# D.3 Reconciliation Walkthrough (Operator Guide)

Issue: #719

Status: docs-only glossary + reading guide. No submit. No broker actions.

## Purpose

Make D.3 reconciliation states operator-readable so the operator can interpret supervision and reconciliation without JSON archaeology.

This supports #669 but does not replace the operator signature.

## Source of Truth

- `docs/supervised-broker-runbook.md`
- `docs/d3-hardening-and-promotion-criteria.md`
- `docs/ops/d3-operator-hardening-declarations.md` (#669)

## How to Read Reconciliation (Without Archeology)

Operational rule:

- Prefer the latest operator-facing summary artifact for the session.
- Only open raw JSON payloads if the summary contradicts itself or is missing required fields.
- Stop on ambiguity. Do not retry, resubmit, or improvise a “best guess”.

Operator reading order (conceptual):

1. Identify the target session (the operator’s chosen `latest_session`).
2. Check `root_alert_status` (is there an escalation that blocks continuation?).
3. Determine whether the session is in a terminal or non-terminal state.
4. If non-terminal or ambiguous, stop and escalate.
5. If terminal, record the result and proceed to the next governed step (never skip reconciliation).

## Glossary (Minimum Terms)

### `submitted_remote`

- Meaning: a broker submit attempt was performed and there is evidence the venue received it.
- Operator interpretation: treat as “order exists remotely unless proven otherwise”.
- Continue/Stop rule: stop if the remote identifiers are missing or if status remains `unknown` after the defined reconciliation steps.

### `reconciliation_required`

- Meaning: the system cannot prove the remote order identity or lifecycle conclusively from the existing evidence.
- Operator interpretation: this is an escalation state, not a normal intermediate.
- Continue/Stop rule: stop immediately. Do not retry submit. Follow the runbook’s reconciliation procedure until the state becomes terminal.

### `filled`

- Meaning: the order was filled (partially or fully) and fill evidence exists.
- Operator interpretation: exposure likely exists or existed. The next question is whether it is still open and whether a close is required.
- Continue/Stop rule: continue only if the runbook confirms the position is closed or a governed reduce-only close plan is in place.

### `closed`

- Meaning: the position/order lifecycle is closed and the evidence supports no open exposure.
- Operator interpretation: it is safe to treat the session as complete from an exposure standpoint.
- Continue/Stop rule: continue to artifact capture and reporting; do not reopen or “improve” the session.

### `rejected`

- Meaning: the venue rejected the submit, and the evidence supports that no order exists remotely.
- Operator interpretation: no exposure is expected, but the reason should be recorded.
- Continue/Stop rule: continue only after the rejection is understood and recorded. Do not retry blindly.

### `ambiguous`

- Meaning: evidence conflicts or is insufficient to classify the session safely.
- Operator interpretation: treat as unsafe. Assume there may be exposure until proven otherwise.
- Continue/Stop rule: stop and escalate through the reconciliation steps. No retries, no new submits.

### `unknown`

- Meaning: the system cannot classify the remote state from available evidence and probes.
- Operator interpretation: treat as ambiguous until reconciliation produces a deterministic classification.
- Continue/Stop rule: stop. Do not proceed to any action that assumes the exposure is known.

### `terminal`

- Meaning: a state that ends the session classification for this drill (e.g., `closed`, `rejected`, deterministically `filled` with close completed).
- Operator interpretation: the session can be archived as evidence; no further broker action is required for classification.
- Continue/Stop rule: continue to evidence capture only.

### `non_terminal`

- Meaning: a state that requires further reconciliation or supervision steps (e.g., `submitted_remote`, `unknown`, `reconciliation_required`).
- Operator interpretation: the session is not finished; additional governed checks are required.
- Continue/Stop rule: do not treat the session as complete. Stop on ambiguity.

### `latest_session`

- Meaning: the currently selected session used as the “active” operator context.
- Operator interpretation: always record which session is being interpreted to avoid mixing evidence across sessions.
- Continue/Stop rule: stop if the operator cannot identify the correct session id deterministically.

### `root_alert_status`

- Meaning: the top-level alert severity derived from session evidence.
- Operator interpretation: alerts are the gate. Critical means “stop and reconcile”, not “continue carefully”.
- Continue/Stop rule: stop on `critical` or any alert that indicates reconciliation is required.

## State Transition Interpretation (Operator Notes)

Common safe transition patterns (conceptual):

- `submitted_remote` -> `filled` -> `closed`
- `submitted_remote` -> `rejected` (terminal)

Escalation patterns:

- `submitted_remote` -> `reconciliation_required` (stop)
- `unknown` -> `reconciliation_required` (stop)
- any -> `ambiguous` (stop)

## Evidence Reference

This walkthrough should be used to interpret existing D.3 evidence (e.g., #446) without requiring a new submit.

## Operator Memo (Template)

Create a memo under `docs/ops/` using:

```yaml
memo_type: d3_reconciliation_walkthrough
issue: 719
date: YYYY-MM-DD
operator: "<name or handle>"
submit_performed: false
broker_actions_performed: false
supports_declaration:
  issue: 669
  declaration: "D.3 reconciliation interpretation"
evidence_reference:
  issue: 446
  session_id: "<id>"
  artifacts_path: "outputs/<...>/"
reading:
  latest_session: "<id>"
  root_alert_status: "<value>"
classification:
  state: "<one of: submitted_remote|reconciliation_required|filled|closed|rejected|ambiguous|unknown>"
  terminal: true|false
stop_rule:
  continue: "<what makes it safe to continue>"
  stop: "<what makes it unsafe>"
notes:
  - "<any ambiguity or runbook improvements>"
```

## Acceptance Checklist

- Glossary exists and includes all minimum terms.
- Each term includes meaning, operator interpretation, and continue/stop rule.
- Includes stop-on-ambiguity guidance and reading order.
- References existing D.3 evidence (#446) as the target for interpretation.
- States it supports #669 but does not replace operator signature.

