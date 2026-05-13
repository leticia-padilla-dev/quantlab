# Stage E Alert Confidence Matrix (Expected / Acceptable / Blocking)

Issue: [#739](https://github.com/Whiteks1/quantlab/issues/739)

Date: 2026-05-13

Status: docs-only matrix. No runtime changes.

## Inputs

- `docs/ops/stage-e-scoping.md`
- `docs/ops/stage-e-checklist.md`
- `docs/ops/stage-e-evidence-index.md`
- `docs/ops/d3-repeatability-criteria.md`
- `docs/d3-hardening-and-promotion-criteria.md`
- `docs/supervised-broker-runbook.md`

## Global Rule (Must Remain True)

```yaml
stage_e:
  status: blocked
  docs_only_default: true
```

## Interpretation Model

This matrix classifies alert and state signals into four buckets:

```yaml
alert_model:
  expected: "Normal given preserved evidence; requires correct interpretation."
  acceptable: "Not ideal, but does not block review if explained and bounded."
  escalation_required: "Operator must stop, reconcile, and/or document before continuing."
  blocking: "Stop. Repeatability gate fails until resolved."
```

## Root vs Latest (Non-Negotiable)

Definitions:

```yaml
root_level:
  meaning: "aggregate posture across sessions; preserves historical evidence"
latest_session:
  meaning: "most recent session state; used to evaluate the current cycle outcome"
```

Rule:

- Root-level `critical` can coexist with latest-session `ok` when historical rejected sessions are preserved as evidence.
- Any interpretation that treats root-level `critical` as “the latest session failed” is invalid.

## Matrix

### A) Aggregate Alerts (Root-Level)

| Signal | Expected | Acceptable | Escalation Required | Blocking |
|---|---|---|---|---|
| `root alert_status: critical` explained by historical rejected sessions | ✅ | ✅ | ⛔ | ⛔ |
| `root alert_status: critical` and operator cannot explain why | ⛔ | ⛔ | ✅ | ✅ |
| Root-level counts increase unexpectedly (new critical category appears) | ⛔ | ⛔ | ✅ | ✅ |

Operator action when escalation/blocking:

- Stop review of “promotion readiness”.
- Inspect the evidence index anchors and document the reason for escalation.

### B) Latest Session State (Session-Level)

| Signal | Expected | Acceptable | Escalation Required | Blocking |
|---|---|---|---|---|
| Latest session is terminal and reconciled (`filled/closed`) | ✅ | ✅ | ⛔ | ⛔ |
| Latest session is terminal but reconciliation is unclear | ⛔ | ⛔ | ✅ | ✅ |
| Latest session state regresses (was known terminal, later appears unknown) | ⛔ | ⛔ | ✅ | ✅ |

### C) Reconciliation Ambiguity

Reference gates:

- `docs/ops/d3-repeatability-criteria.md` → `reconciliation_requirements` + `blocking_conditions`

| Signal | Expected | Acceptable | Escalation Required | Blocking |
|---|---|---|---|---|
| `reconciliation_state: filled` with consistent order status | ✅ | ✅ | ⛔ | ⛔ |
| `reconciliation_state: reconciliation_required` | ⛔ | ⛔ | ✅ | ✅ |
| Identifiers missing (`oid/cloid`) after submit acknowledgement | ⛔ | ⛔ | ✅ | ✅ |
| Operator cannot classify the state without reading raw JSON | ⛔ | ⛔ | ✅ | ✅ |

Stop rule:

```yaml
stop_on_ambiguity:
  if_reconciliation_unclear: true
  do_not_open_second_session: true
  do_not_retry_submit: true
```

### D) Stale Detection

Stale is treated as an operator-safety signal. It may be acceptable as evidence only if it is correctly classified and does not trigger retry widening.

| Signal | Expected | Acceptable | Escalation Required | Blocking |
|---|---|---|---|---|
| Stale is detected and classified using existing alert/health surfaces | ✅ | ✅ | ⛔ | ⛔ |
| Stale detection exists only as anecdote (no artifact-backed evidence) | ⛔ | ⛔ | ✅ | ✅ |
| Stale leads to “try again” execution behavior | ⛔ | ⛔ | ✅ | ✅ |

### E) Supervision States

Supervision is evidence of operational discipline, not an execution authorization.

| Signal | Expected | Acceptable | Escalation Required | Blocking |
|---|---|---|---|---|
| `hyperliquid_supervision.json` exists for a terminal session | ✅ | ✅ | ⛔ | ⛔ |
| No supervision artifacts exist, but operator can still reconcile and classify outcomes | ⛔ | ✅ | ✅ | ⛔ |
| Supervision exists but conflicts with reconciliation truth | ⛔ | ⛔ | ✅ | ✅ |

## Required Navigation Paths

These are the minimum evidence surfaces the operator must be able to locate (see `docs/ops/stage-e-evidence-index.md`):

```yaml
required_paths:
  - hyperliquid_submits_health: outputs/hyperliquid_submits/hyperliquid_submits_health.json
  - hyperliquid_submits_alerts: outputs/hyperliquid_submits/hyperliquid_submits_alerts.json
  - reconciliation_entry: outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49/hyperliquid_reconciliation.json
  - reconciliation_close: outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8/hyperliquid_reconciliation.json
```

## Escalation Recording Template

Use this when an escalation or blocking condition occurs.

```yaml
alert_escalation_record:
  date: null
  trigger: null
  classification: escalation_required_or_blocking
  operator_action: null
  evidence_paths:
    - null
  notes: null
```

## Out of Scope

- No runtime changes.
- No retry-loop semantics.
- No automation widening.
- No Stepbit work.
