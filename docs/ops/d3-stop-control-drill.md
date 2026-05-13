# D.3 Stop-Control Decision Table (Operator Guide)

Issue: #720

Status: docs-only decision table + drill memo template. No submit. No broker actions.

## Purpose

Make stop-control operator-readable.

The operator must be able to distinguish:

- when cancel is correct
- when cancel is forbidden / unsafe
- when reduce-only close is required
- when the exchange UI is a last-resort emergency fallback only

This supports #669 but does not replace the operator signature.

## Source of Truth

- `docs/supervised-broker-runbook.md`
- `docs/d3-hardening-and-promotion-criteria.md`
- `docs/ops/d3-operator-hardening-declarations.md` (#669)

## Non-Negotiable Rules

- No retry on ambiguity.
- Stop on ambiguity.
- Never take an action that assumes exposure is known unless reconciliation proves it.
- UI fallback is last resort only, and must be treated as an emergency boundary (record and halt).

## Decision Table

| situation | correct action | forbidden action | required artifact/check | stop rule |
|---|---|---|---|---|
| Order not submitted (no submit attempt exists) | Stop. Record “no submit performed”. | Submit, cancel, or “test” the venue. | Evidence shows no submit attempt in the session artifacts. | Stop immediately. No action is authorized by this issue. |
| Submit attempted but remote identifiers missing | Enter `reconciliation_required` posture. Escalate via reconciliation procedure. | Retry submit. Assume “probably fine”. | Submit response artifact + check for missing `oid/cloid` or equivalent. | Stop until deterministic identity is recovered or session is classified terminal. |
| Submitted but not filled (exposure not present yet) | Follow runbook: supervised cancel may be considered only if identity is deterministic and cancel is governed. | Reduce-only close (no exposure). UI action (not needed). | Remote order identity must be proven; status must be known. | Stop if status is `unknown`/`ambiguous` or identity is missing. |
| Filled with open exposure (position exists) | Reduce-only close is required (governed close plan). | Cancel (cannot remove exposure). Retry submit. | Fill evidence + position/open exposure evidence + reconciliation shows exposure is open. | Stop if exposure cannot be proven closed after attempted close steps. |
| Filled and closed (no open exposure) | Stop. Capture evidence. | Re-open, “improve”, or re-run the session. | Reconciliation + fill summary shows closed state. | Stop if any artifact contradicts “closed”. |
| Reconciliation is ambiguous (conflicting evidence) | Stop and escalate. Only proceed when reconciliation becomes deterministic. | Any action that assumes exposure is known. | Reconciliation artifact indicates ambiguity/unknown state. | Stop immediately. No retries. |
| Reduce-only close required but unclear parameters | Stop. Escalate for clarification. | Guess sizing or side. | Runbook checklist + intent preconditions must be satisfied. | Stop until parameters are governed and verified. |
| Venue UI emergency fallback (systems/CLI unreliable) | Emergency-only: use UI to reduce risk, then halt and record. | Treat UI as normal workflow. | Document why CLI/runbook path was unavailable; capture screenshots/notes as evidence. | Stop after UI intervention and create an incident memo. |

## Mapping Notes (Cancel vs Reduce-Only Close)

- Cancel is only meaningful when the order is not filled and exposure does not exist.
- Reduce-only close is only meaningful when exposure exists (filled/open position).
- If the system cannot prove which of those is true, the correct action is to stop and reconcile.

## Drill Memo (Template)

Create a memo under `docs/ops/`:

```yaml
memo_type: d3_stop_control_drill
issue: 720
date: YYYY-MM-DD
operator: "<name or handle>"
submit_performed: false
broker_actions_performed: false
supports_declaration:
  issue: 669
  declaration: "D.3 stop-control: cancel vs reduce-only close"
evidence_reference:
  issue: 446
  session_id: "<id>"
  artifacts_path: "outputs/<...>/"
table_application:
  - situation: "<one of the table situations>"
    chosen_action: "<correct action>"
    forbidden_actions_considered:
      - "<forbidden action 1>"
    required_checks_used:
      - "<artifact/check>"
    stop_rule_applied: "<what would make you stop>"
notes:
  - "<any runbook ambiguity or improvement request>"
```

## Acceptance Checklist

- Decision table exists with columns:
  - situation
  - correct action
  - forbidden action
  - required artifact/check
  - stop rule
- Table covers:
  - order not submitted
  - submitted but not filled
  - filled/open exposure
  - ambiguous reconciliation
  - reduce-only close required
  - UI emergency fallback
- Memo template exists and references existing D.3 evidence (e.g., #446) without new submit.
- States it supports #669 but does not replace operator signature.

