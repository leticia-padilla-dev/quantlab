# Baseline Candidate Promotion

## Purpose

Declare a specific shortlisted config as the `baseline_candidate` for
supervised paper trial consideration.

This is a separate, explicit operator decision. A shortlisted config is
not automatically a baseline candidate.

Only one config may hold `baseline_candidate` status at a time.

---

## Trigger

This step applies only when:

- At least one config has passed the candidate shortlist gates (#635)
- A candidate memo has been completed and approved for that config
- The operator has reviewed and is ready to make a promotion decision

---

## Promotion Checklist (all required)

| Item | Requirement |
|------|-------------|
| Shortlist status | Config appears in `docs/research/shortlist.csv` |
| Candidate memo | `docs/research/candidate-memos/<config_id>-memo.md` exists and is complete |
| Artifacts verified | `report.json` and `robustness_verdict.json` exist in `outputs/runs/<run_id>/` |
| Benchmark comparison | `Benchmark` column is `pass` (not `pending`, `blocked`, or `warn:` without justification) |
| Config hash | `config_hash` is recorded and matches the config file |
| No prior baseline | No other config currently holds `baseline_candidate` status (or prior baseline is explicitly superseded with documented reason) |
| Operator decision | Explicit written decision recorded in candidate memo and decision matrix |

---

## Promotion Process

1. Confirm all checklist items are true
2. Update `docs/research/config-decision-matrix.md`:
   - Set `Decision` to `PASS`
   - Add `baseline_candidate:true` to the `Memo` column
3. Update `docs/research/shortlist.csv`:
   - Set `operator_decision` to `baseline_candidate`
4. Record promotion in candidate memo (`docs/research/candidate-memos/<config_id>-memo.md`):
   - Add `## Baseline Candidate Declaration` section with date and rationale
5. If superseding a prior baseline candidate: document the reason explicitly

---

## What Baseline Candidate Status Enables

- Planning of `paper_strategy_trial` (see #639)
- Completion of the `before_paper_execution` checklist

Baseline candidate status does NOT:
- Authorize paper execution by itself
- Constitute D.3 evidence
- Authorize broker submission
- Authorize live execution
- Remove any other gate requirement

---

## Baseline Candidate Declaration Template

Add this section to the candidate memo when promotion is made:

```markdown
## Baseline Candidate Declaration

- Date: <YYYY-MM-DD>
- Declared by: <operator>
- Config ID: <C001 / C002 / …>
- Config hash: <hash>
- Run ID: <run_id>
- Supersedes: <prior baseline_candidate config_id or 'none'>
- Rationale: <one or two sentences>

This config is declared baseline_candidate. It is eligible for
paper_strategy_trial planning. No paper execution occurs without
completing the before_paper_execution checklist (see
docs/paper-readiness-checklist.md).
```

---

## Current Baseline Candidate

| Field | Value |
|-------|-------|
| Config ID | — (none declared) |
| Config File | — |
| Run ID | — |
| Declaration Date | — |
| Memo | — |

*This table is updated when a baseline candidate is declared.*

---

## Revocation

A baseline candidate may be revoked if:

- A new robustness run reveals disqualifying evidence
- The config file is modified after hash lock
- The operator determines the evidence does not support continued trial preparation

Revocation must be documented in the candidate memo and decision matrix.
