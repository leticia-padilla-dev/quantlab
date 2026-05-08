# Supervised Paper — Readiness Checklist and Success Metrics

## Purpose

Paper trading is not about making money. Paper trading validates that the
strategy behaves as designed, that the operator has control, and that
artifacts are complete and recoverable.

A paper session that shows positive PnL but fails execution integrity checks
is **not a success**.

A paper session that shows neutral PnL but passes all integrity checks
**is a success**.

---

## Before Paper Execution Checklist

Applies to `paper_strategy_trial` mode only (see `docs/paper-modes-governance.md`).
Infrastructure smoke does not require this checklist.

| Item | Requirement | Status |
|------|-------------|--------|
| `baseline_candidate_exists` | Config declared as baseline candidate in decision matrix | — |
| `candidate_memo_approved` | Candidate memo reviewed and shortlist decision recorded | — |
| `paper_infrastructure_smoke_passed` | Infrastructure smoke session completed separately | — |
| `expected_behavior_defined` | Entry, exit, and hold behavior documented in writing | — |
| `stop_conditions_defined` | Hard and soft stops defined before session begins | — |
| `operator_can_follow_runbook` | Operator has read and rehearsed the runbook | — |
| `artifacts_expected_are_defined` | Expected artifact paths listed before session | — |
| `config_hash_locked` | Config file frozen; hash matches decision matrix | — |

All items must be `true` before a paper strategy trial session begins.
No item may be completed retroactively.

---

## Paper Success Criteria

### execution_integrity

| Criterion | Pass condition |
|-----------|----------------|
| Critical execution errors | 0 critical errors during session |
| Order traceability | Every simulated order has a traceable artifact entry |
| Rejects | No unexplained rejects |
| Reconciliation | Session reconciliation completes without unresolved discrepancies |

### behavior_consistency

| Criterion | Pass condition |
|-----------|----------------|
| Entry/exit behavior | Matches documented expected behavior |
| Config changes | Zero config changes during session |
| Drawdown | Within predefined tolerance band (defined in stop conditions) |
| Turnover | Not materially higher than expected from backtest |

### operator_control

| Criterion | Pass condition |
|-----------|----------------|
| Session state | Operator can explain current state at any point |
| Ambiguity handling | Operator identifies and escalates ambiguous states |
| Session stop | Operator can execute clean stop per runbook |

---

## Paper Success Does NOT Require

- Positive PnL per session
- High trade count
- Specific return threshold
- Beating any benchmark

Paper success is about process and control, not outcome.

---

## Stop Conditions

Stop conditions must be defined **before** the session begins and may not
be modified after seeing session results.

### Hard Stops (session must end immediately)

| Condition | Action |
|-----------|--------|
| Any critical execution error not attributable to infrastructure | Stop session; log artifact |
| Drawdown exceeds predefined tolerance band | Stop session; record cause |
| Session enters unobservable state | Stop session; escalate |
| Artifact writes fail silently | Stop session; investigate |
| Config drift detected (config hash mismatch) | Stop session; investigate |

### Soft Stops (operator review required before continuing)

| Condition | Action |
|-----------|--------|
| Turnover materially higher than expected | Pause; document observation; decide |
| Entry/exit pattern diverges from expected behavior | Pause; document; decide |
| Reconciliation discrepancy detected | Pause; investigate; resolve before continuing |
| Any unexpected state not covered by runbook | Pause; escalate |

---

## Paper Session Output Artifacts

After a session, the following artifacts must be recoverable:

| Artifact | Description |
|----------|-------------|
| Session log | Full timestamped session log |
| Simulated order record | All orders placed with status |
| Reconciliation output | Session reconciliation summary |
| Operator notes | Observations recorded during session |
| Session status | Explicit terminal status (`complete` / `stopped` / `failed`) |

If any artifact is missing, the session is incomplete regardless of PnL.

---

## Paper Success Opens

A successful paper strategy trial opens **D.3 review eligibility** — not D.3 auto-approval.

D.3 review requires a separate explicit decision. A successful paper session
alone does not authorize:
- Micro-live execution
- Capital deployment
- Broker submit
- Stage E consideration
- Automation

---

## Escalation Levels for Paper Strategy Trial

Referenced from issue #639 (paper strategy trial plan):

| Level | Duration | Objective |
|-------|----------|-----------|
| level_1_dry_run | 1 session | Minimal strategy-paper lifecycle validation |
| level_2_short_series | 3–5 sessions | Consistency and artifact stability |
| level_3_hardened_series | 10+ sessions or 2+ weeks | Repeatability and operator control confidence |

Success criteria apply at each level. A level does not pass if hard stop
conditions were triggered and not resolved.
