# Supervised Paper Strategy Trial Plan

## Purpose

Define the escalating session plan for a paper strategy trial. This plan
prepares the structure — it does not execute paper sessions.

No paper execution occurs from this document alone.
A baseline candidate and completed before_paper_execution checklist are
required before any session begins (see `docs/paper-readiness-checklist.md`).

---

## Trigger

This plan applies only when:

- A baseline candidate is declared (see `docs/research/baseline-candidate-promotion.md`)
- The candidate shortlist gates have been passed (#635)
- Infrastructure smoke has passed (see `docs/paper-infrastructure-smoke-v1.md`)

---

## Escalation Levels

### level_1_dry_run

| Property | Value |
|----------|-------|
| Sessions | 1 |
| Objective | Minimal strategy-paper lifecycle validation |
| Success criteria | All execution_integrity items pass; session terminates cleanly |
| Advancement condition | level_1 passes all hard stop criteria |
| Promotes to | level_2_short_series (not baseline; not paper approval) |

**Specific stop conditions for level_1:**
- Any critical execution error → stop; do not advance to level_2
- Session does not terminate cleanly → investigate; do not advance
- Artifacts missing after session → investigate; do not advance

---

### level_2_short_series

| Property | Value |
|----------|-------|
| Sessions | 3–5 |
| Objective | Consistency and artifact stability |
| Success criteria | No hard stops triggered; artifacts consistent across sessions; behavior matches expectation |
| Advancement condition | All sessions complete with no unresolved soft stops |
| Promotes to | level_3_hardened_series |

**Specific stop conditions for level_2:**
- Two or more sessions trigger a hard stop → stop series; investigate
- Artifact inconsistency across sessions → stop; investigate
- Turnover consistently higher than expected → document; decide before continuing

---

### level_3_hardened_series

| Property | Value |
|----------|-------|
| Sessions | 10+ sessions or 2+ weeks (whichever is longer) |
| Objective | Repeatability, operator control, reconciliation confidence |
| Success criteria | Consistent execution across sessions; no unresolved hard stops; operator demonstrates full control |
| Advancement condition | Completes all sessions with documented operator notes |
| Opens | D.3 review eligibility (not D.3 auto-approval) |

**Specific stop conditions for level_3:**
- Any session triggers a hard stop that repeats in a subsequent session → escalate
- Reconciliation discrepancy not resolved within one session → pause series
- Operator cannot maintain observation → pause series

---

## Operator Notes Template

Record after each session:

```
session_notes:
  level: <level_1 / level_2 / level_3>
  session_number: <n>
  date: <YYYY-MM-DD>
  config_id: <C001 / C002 / …>
  run_id: <run_id>
  hard_stops_triggered: <none / describe>
  soft_stops_triggered: <none / describe>
  behavior_matches_expectation: <yes / partially / no — explain>
  artifacts_complete: <yes / no — describe if no>
  reconciliation_status: <clean / discrepancy — describe>
  operator_notes: <free text>
  advancement_decision: <advance / hold / stop — explain>
```

---

## What Each Level Does NOT Open

| Level completes | Does NOT open |
|-----------------|---------------|
| level_1 | live execution, D.3, broker submit |
| level_2 | live execution, D.3, broker submit |
| level_3 | live execution, Stage E, broker submit, automated execution |

Level 3 completion opens D.3 **review eligibility only**. D.3 requires a
separate explicit decision with a pre-D.3 checklist (see #640).

---

## Stop and Resume Policy

A series may be paused and resumed if:

- The stop condition is investigated and resolved
- The resolution is documented in operator notes
- The operator confirms readiness before resuming

A series may not resume without documented resolution.
