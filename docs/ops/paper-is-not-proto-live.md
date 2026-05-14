# Paper is Not Proto-Live

Issue: [#762](https://github.com/Whiteks1/quantlab/issues/762)

Status: docs-only. No runtime changes. No submit. Stage E remains blocked.

## Purpose

Prevent semantic drift where paper operations become psychologically treated as “almost live”.

Paper is an evidence system and an operator discipline system:

- deterministic artifacts
- deterministic interpretation
- governed stop semantics

Paper is not broker execution, not Stage E, and not a proxy for live-readiness.

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Allowed Statements (Paper)

```yaml
allowed_claims:
  - "Artifacts are complete and navigable."
  - "Two operators reach the same conclusion from the same artifacts."
  - "Stop-on-ambiguity is enforced; no retry loops."
  - "Observability aggregates are deterministic summaries, not truth."
```

## Forbidden Statements (Paper)

```yaml
forbidden_claims:
  - "We are basically live."
  - "Paper success implies broker readiness."
  - "Promotion is automatic."
  - "It worked once, therefore it is safe."
```

## Allowed Actions (Paper)

```yaml
allowed_actions:
  - "Run a paper session via the runbook."
  - "Inspect artifacts under outputs/paper_sessions/<session_id>/."
  - "Generate paper health/alerts and preserve them as artifacts."
  - "Stop and document when ambiguous."
```

## Forbidden Actions (Paper)

```yaml
forbidden_actions:
  - "Any broker submit or broker action."
  - "Retry loops under ambiguity."
  - "Auto-fixes that change decisions without operator review."
  - "Treating observability summaries as execution authority."
```

## Required Language (Ops Hygiene)

When describing work in issues, PRs, or memos:

- Say “paper evidence” and “paper observability”, not “proto-live”.
- Say “stop-on-ambiguity”, “no retry”, and “no broker actions” explicitly.
- When referencing “promotion”, qualify it as “spec-only / handoff-only / no authority”.

## References

- `docs/paper-session-runbook.md`
- `docs/ops/paper-session-terminality-contract.md`
- `docs/ops/paper-artifact-completeness-contract.md`
- `docs/ops/paper-operator-interpretation-contract.md`
- `docs/ops/paper-canonical-vs-observability-boundary.md`

## Non-Goals

- This document does not define strategy performance evaluation.
- This document does not authorize broker work.
- This document does not open Stage E.
