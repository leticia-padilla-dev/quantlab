# D.3 Repeatability Criteria (Operational Minimums)

Issue: [#738](https://github.com/Whiteks1/quantlab/issues/738)

Date: 2026-05-13

Status: criteria-only. No runtime changes.

## Purpose

Define what “repeatability sufficient” means in operational terms for the D.3 supervised corridor, so Stage E scoping and future runtime proposals can be evaluated against explicit gates instead of optimism.

This document does not open Stage E.

## Source of Truth

- `docs/d3-hardening-and-promotion-criteria.md`
- `docs/supervised-broker-runbook.md`
- `docs/ops/stage-e-scoping.md` (scoping boundary; Stage E remains blocked)
- `docs/ops/stage-e-checklist.md` (E0)
- `docs/ops/stage-e-evidence-index.md` (E1)
- `docs/ops/d3-operator-hardening-declarations.md` (issue #669)

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  scoping_issue: 734
  runtime_open: false
```

## Repeatability Definition

Repeatability is satisfied only when the operator can execute and supervise the corridor in a way that is:

- runbook-driven (no hidden context required)
- artifact-complete (evidence is durable and navigable)
- ambiguity-governed (stop rules prevent “keep trying” behavior)
- operator-readable (decisions can be made without raw JSON archaeology)

## Operational Minimums

```yaml
repeatability:
  minimum_sessions:
    description: "Minimum number of supervised sessions required to claim corridor repeatability."
    required:
      entry_and_close_cycles:
        count: 2
        constraint: "Each cycle must include an entry session and a reduce-only close session."
      supervision_samples:
        count: 2
        constraint: "At least two supervision artifacts exist for terminal sessions."

  allowed_failure_modes:
    description: "Failure modes that are acceptable as evidence, provided they are correctly classified and do not widen execution."
    allowed:
      - submit_rejected_preserved_as_evidence
      - reconciliation_required_and_stopped
      - alert_critical_explained_by_historical_rejections
    not_allowed:
      - ambiguity_followed_by_second_submit_attempt
      - operator_uncertain_but_execution_continues
      - missing_identifiers_treated_as_success

  escalation_thresholds:
    description: "When the operator must escalate or stop."
    required:
      - condition: "reconciliation_state is unclear or reconciliation_required persists"
        action: "stop_and_reconcile; do_not_open_second_session"
      - condition: "submit acknowledgement missing identifiers (oid/cloid)"
        action: "treat_as_reconciliation_required; stop"
      - condition: "operator cannot explain current state using runbook surfaces"
        action: "stop"

  blocking_conditions:
    description: "If any are true, repeatability is not satisfied."
    blocking:
      - "operator_declarations_incomplete"
      - "evidence_paths_missing_or_modified"
      - "no_reduce_only_close_proof"
      - "stop_rules_not_followed_under_ambiguity"
      - "requires_raw_json_archaeology_for_core_decisions"

  reconciliation_requirements:
    description: "Minimum reconciliation evidence required for repeatability."
    required:
      - "hyperliquid_reconciliation.json exists for each session in the cycle"
      - "normalized terminal classification exists (filled/closed OR reconciliation_required with stop)"
      - "no state regression that hides known reconciliation truth"

  stop_control_requirements:
    description: "Stop-control requirements for a filled perp position."
    required:
      - "reduce-only close is used as the primary stop-control mechanism"
      - "emergency UI close is last resort only when QuantLab artifacts are unavailable or ambiguous"
      - "any emergency UI close triggers follow-up reconciliation and documentation"

  operator_interpretability:
    description: "Operator must be able to interpret outcomes without raw JSON archaeology."
    required:
      - "operator can explain: submitted_remote vs reconciliation_required vs filled"
      - "operator can explain: root critical vs latest ok"
      - "operator can locate evidence via E1 index paths"
      - "operator follows stop-on-ambiguity rule"
```

## Evidence Anchors (Current Known Sessions)

These are anchors for navigation and discussion. They do not by themselves satisfy the minimum session counts.

```yaml
anchors:
  entry_session: outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49
  reduce_only_close_session: outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8
```

## Decision Output (How to Use This Doc)

```yaml
decision:
  if_repeatability_satisfied: "Stage E scoping can propose a first narrow runtime slice (still requires explicit authorization)."
  if_repeatability_not_satisfied: "Continue docs-only operationalization and evidence generation; do not propose runtime widening."
```
