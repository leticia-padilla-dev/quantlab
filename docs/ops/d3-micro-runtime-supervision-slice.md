# D.3 Micro-Runtime Supervision Slice (Operator Procedure)

Issue: #798

Status: docs-only. No runtime changes. No submit automation. Stage E remains blocked.

## Objective

Define the first supervised D.3 micro-runtime workflow as an operator procedure.

This slice turns the existing Hyperliquid evidence contract into an executable workflow without changing runtime behavior.

## Scope / Constraints

```yaml
scope:
  docs_only: true
  runtime_changes: false
  submit_allowed_by_this_slice: false
  broker_changes: false
  automation: false
  stage_e: blocked
  outputs_versioned: false
```

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## References (Source of Truth)

- [supervised-broker-runbook.md](../supervised-broker-runbook.md)
- [hyperliquid-submit-session-evidence-contract.md](./hyperliquid-submit-session-evidence-contract.md)
- [d3-reconciliation-walkthrough.md](./d3-reconciliation-walkthrough.md)
- [d3-operator-hardening-declarations.md](./d3-operator-hardening-declarations.md)
- [stage-e-runtime-slice-policy.md](./stage-e-runtime-slice-policy.md)
- [d3-stop-control-drill.md](./d3-stop-control-drill.md)

## Authority Boundary Banner (Must Be Treated as True)

```text
NO SUBMIT AUTHORIZED
STAGE_E_BLOCKED
signed_action != submit_authority
```

Interpretation:
- This document defines procedure and stop rules.
- Any submit is governed by separate authorization and explicit operator confirmation.
- If the operator cannot explain exposure deterministically from artifacts, the correct action is stop.

## Required Preconditions (Before Any Entry Submit Is Considered)

All must be true before attempting an entry session:

```yaml
preconditions:
  operator_present: true
  operator_signature_posture: available
  runbook_available: true
  stop_control_table_understood: true
  reconciliation_walkthrough_understood: true
  evidence_contract_understood: true
  environment_ready:
    - identity_wiring_validated
    - signer_wiring_validated
    - key_resolution_validated
    - nonce_scope_validated
    - deterministic_quantization_validated
    - signed_action_generation_validated
```

If any precondition is false: stop and do not attempt submit.

## Micro-Runtime Design Constraints

```yaml
micro_runtime:
  entry:
    size_policy: tiny
    operator_present: mandatory
    sessions_allowed: 1
  reconciliation:
    mandatory: true
    must_be_deterministic_before_any_new_session: true
  close:
    reduce_only: true
    allowed_only_if_reconciliation_proves_exposure: true
    forbidden_if_reconciliation_ambiguous: true
```

## Session Model

This slice describes two sessions:

1) entry session (tiny)  
2) optional reduce-only close session (only if required by reconciliation evidence)

The close session is forbidden unless the entry session evidence proves exposure exists and a reduce-only close is required.

## Procedure (Operator Steps)

### Step 0 — Confirm the “No-New-Session” Gate

Before opening an entry session, check that no freeze condition is currently active:

- `outputs/hyperliquid_submits/hyperliquid_submits_alerts.json`
- `outputs/hyperliquid_submits/hyperliquid_submits_health.json`

Stop if:
- root alerts are `critical` for reconciliation or missing identifiers
- any existing session is in `reconciliation_required` posture

### Step 1 — Prepare Entry Intent (Tiny)

Entry intent must be tiny and fully deterministic:

- `size_decimals` comes from venue preflight
- quantization uses `floor`
- signed action envelope exists and is signed

Stop if:
- `signature_state != signed`
- `readiness_reasons != []`
- any evidence is missing or inconsistent

### Step 2 — Submit Entry Session (Supervised Only)

Submit is permitted only under explicit operator presence and the runbook’s supervised submit requirements.

Record:
- session id
- outputs path
- reviewer identity and submit note (if applicable)

### Step 3 — Evidence Pack Check (Immediately After Submit)

Apply the Hyperliquid submit session evidence contract to the entry session.

Hard stop if any required minimum artifact is missing or not parseable.

### Step 4 — Reconciliation (Mandatory)

Run reconciliation until the state becomes deterministic.

Stop conditions:
- `reconciliation_required`
- `unknown`
- `ambiguous`
- missing identifiers

No-new-session rule:
- do not open a second entry session while reconciliation is not deterministic.

### Step 5 — Decide Whether Close Is Required

If reconciliation proves no exposure exists (e.g., rejected with deterministic evidence): stop and archive.

If reconciliation proves exposure exists and remains open: proceed to a reduce-only close session only if:

- the runbook defines the close plan deterministically
- reduce-only is guaranteed
- the operator can explain the intended effect and stop conditions

If any of those are not true: stop.

### Step 6 — Reduce-Only Close Session (Conditional)

Close session constraints:

- `reduce_only: true`
- one session only
- same evidence pack rules as entry session
- reconciliation mandatory after close

Stop if:
- reduce-only is not provable
- reconciliation is ambiguous at any point

### Step 7 — Terminality and Freeze

Treat the workflow as complete only when:

- entry session is deterministic and archived
- if close session ran, the final reconciliation proves closed state deterministically

If terminality is not provable from artifacts: freeze and stop.

## Freeze / No-New-Session Rules (Operational Summary)

Apply the contract rules as hard policy:

```yaml
policy:
  freeze_if:
    - any required artifact missing
    - reconciliation_required or ambiguous
    - identifiers missing after submit
    - operator cannot explain exposure deterministically from artifacts
  no_new_session_if:
    - freeze_if applies
    - any session in outputs/hyperliquid_submits is still unresolved
```

## Non-Goals

- This slice does not authorize submit by itself.
- This slice does not define automation.
- This slice does not open Stage E.
