# Stage E Runtime Slice Authorization Policy

Issue: [#740](https://github.com/Whiteks1/quantlab/issues/740)

Date: 2026-05-13

Status: policy-only. No runtime changes.

## Purpose

Define the authorization policy for any future Stage E runtime slice, including scope limits, rollback rules, validation boundaries, and explicit prohibitions against hidden runtime coupling.

This document does not open Stage E.

## Inputs

- `docs/ops/stage-e-scoping.md` (Stage E remains blocked)
- `docs/ops/stage-e-checklist.md` (E0)
- `docs/ops/stage-e-evidence-index.md` (E1)
- `docs/ops/d3-repeatability-criteria.md` (E2)
- `docs/ops/stage-e-alert-confidence-matrix.md` (E3)
- `docs/d3-hardening-and-promotion-criteria.md`
- `docs/supervised-broker-runbook.md`

## Global Rule (Must Remain True)

```yaml
stage_e:
  status: blocked
  docs_only_default: true
  runtime_open: false
```

## Workflow Policy (Non-Negotiable)

```yaml
workflow_policy:
  - one_issue
  - one_branch
  - one_runtime_change
  - one_validation_boundary
  - no_parallel_runtime_slices
```

## Authorization Preconditions

A Stage E runtime slice may be proposed only if:

- E0 checklist is merged and treated as complete for the operator.
- E1 evidence index is merged and usable.
- E2 repeatability criteria exist and are referenced in the runtime slice rationale.
- E3 alert confidence matrix exists and is referenced in the runtime slice rationale.
- A dedicated authorization issue exists for the specific runtime slice (not implied by Stage E existence).

## Runtime Slice Policy

```yaml
runtime_slice:
  max_scope:
    principle: "One behavioral intent per PR."
    allowed:
      - "narrow guard that reduces ambiguity without widening execution authority"
      - "operator-facing classification safety (only if it cannot change runtime behavior)"
    forbidden:
      - "multiple behavior changes packaged as one"
      - "changes that widen execution authority or frequency"
      - "changes that expand venue scope"

  rollback_rule:
    principle: "Rollback must be explicit, fast, and evidence-preserving."
    required:
      - "PR must describe rollback in one paragraph"
      - "rollback must not delete or rewrite evidence artifacts"
      - "rollback must not change historical session classification semantics"

  test_requirement:
    principle: "Any behavior change must be locked by tests."
    required:
      - "pytest coverage for the new or changed behavior"
      - "tests must include at least one ambiguity / edge case"
      - "tests must prove no retry widening occurs"

  evidence_requirement:
    principle: "Runtime work must be justified by evidence, not by preference."
    required:
      - "reference specific evidence paths via E1 index"
      - "reference the specific repeatability gate impacted (E2)"
      - "reference the alert interpretation impact (E3)"
      - "explicitly state what ambiguity is reduced and what remains"

  operator_review_requirement:
    principle: "Operator must be able to reason about the change without raw JSON archaeology."
    required:
      - "operator-readable before/after behavior description"
      - "explicit stop rules preserved"
      - "explicit statement: Stage E remains blocked after merge"
```

## Forbidden: No Hidden Runtime Coupling

The following are explicitly forbidden in any Stage E runtime PR:

```yaml
forbidden:
  - hidden_retries
  - implicit_state_recovery
  - silent_fallback_paths
  - automatic_ambiguity_resolution
  - hidden_runtime_widening_inside_observability
```

Interpretation:

- “Observability” work must not modify behavior.
- If a change can affect execution flow, retries, classification, or state transitions, it is runtime behavior and must be treated as such (scoped, tested, and justified).

## Validation Boundary (Per Runtime PR)

Every runtime PR must include:

```yaml
validation_boundary:
  required:
    - "git diff --check"
    - "pytest (relevant subset at minimum)"
    - "artifact contract review: no silent schema drift"
  forbidden:
    - "manual-only validation with no test coverage"
    - "broad refactors to justify a small behavioral change"
```

## Default Stance

```yaml
default_stance:
  if_uncertain: "do_not_merge; reduce scope; add evidence; restate stop rules"
  if_ambiguous: "stop; reconcile; do_not_retry"
```
