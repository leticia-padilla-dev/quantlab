# D.3 Runbook-Only Reconstruction Drill (No Submit)

Issue: #718

Status: docs-only drill. No submit. No broker actions.

## Purpose

Prove that the operator can reconstruct the D.3 supervised flow using only the runbook, without relying on chat history, memory, or ad hoc interpretation.

This document defines the drill and the required evidence memo. It does not close #669 by itself.

## Source of Truth

- `docs/supervised-broker-runbook.md`
- `docs/d3-hardening-and-promotion-criteria.md`
- `docs/ops/d3-operator-hardening-declarations.md` (#669)

## Drill Constraints (Non-Negotiable)

- No new live submit.
- No broker action.
- No signed action generation.
- No runtime/product code changes.
- Stop immediately on ambiguity.

## What Must Be Reconstructed (Dry)

The operator must be able to reconstruct, in order:

1. Readiness gate and preconditions.
2. Signed action preconditions (conceptual; no generation).
3. Submit gate (conceptual; no submit).
4. Reconciliation model and states.
5. Reduce-only close logic and when it is mandatory.
6. Supervision loop and operator checkpoints.
7. Health / alerts interpretation.

## Required Gates (Operator Checklist)

Before any broker-facing action (not performed in this drill), the operator must be able to list and verify:

- Workspace and runbook version being used.
- Scope confirmation: supervised, evidence-first, reversible.
- Account boundary confirmation (no capital deployment intent).
- Last known position state and whether reconciliation is required.
- Stop-control plan for ambiguous state (cancel vs reduce-only close vs emergency UI).
- Alert visibility path (how to see health and alerts outputs).
- Evidence outputs path (where artifacts live; what is authoritative).

## Stop-On-Ambiguity Rule

The drill must name the exact point where ambiguity forces a stop, for example:

- State cannot be classified from artifacts alone.
- Local view and venue view disagree and reconciliation cannot resolve it.
- Close action would be unsafe due to uncertainty about open exposure.

The memo must state what the operator does next when stopped (e.g., halt, escalate, do not retry).

## Evidence Memo (Template)

Create a memo under `docs/ops/` using the following template:

```yaml
memo_type: d3_runbook_reconstruction_drill
issue: 718
date: YYYY-MM-DD
operator: "<name or handle>"
runbook_source:
  primary: "docs/supervised-broker-runbook.md"
  supporting:
    - "docs/d3-hardening-and-promotion-criteria.md"
    - "docs/ops/d3-operator-hardening-declarations.md"
submit_performed: false
broker_actions_performed: false
supports_declaration:
  issue: 669
  declaration: "D.3 runbook reconstruction"
reconstruction:
  steps:
    - readiness
    - signed_action_preconditions
    - submit_gate
    - reconciliation
    - reduce_only_close
    - supervision
    - health_alerts
gates_checked:
  - "<gate 1>"
  - "<gate 2>"
stop_on_ambiguity:
  stop_point: "<where you would stop>"
  reason: "<why it is ambiguous>"
  next_action: "<halt/escalate/no retry/etc>"
notes:
  - "<any clarification needed in runbook>"
```

## Acceptance Checklist

- Memo exists under `docs/ops/`.
- Memo explicitly states `submit_performed: false` and `broker_actions_performed: false`.
- Memo reconstructs the full D.3 flow sections listed above.
- Memo lists gates and a stop-on-ambiguity point.
- Memo explicitly states which #669 declaration it supports.

