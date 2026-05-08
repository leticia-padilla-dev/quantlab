# Paper Trading Modes — Governance v1

"Paper trading" is not a single concept in QuantLab. There are two distinct
operational modes with different prerequisites, purposes, and restrictions.
Conflating them creates risk: a team can run infrastructure smoke without any
research pass, but cannot run a strategy trial without a baseline candidate.

---

## Two Modes

### paper_infrastructure_smoke

| Field | Value |
|-------|-------|
| requires_research_pass | **false** |
| requires_baseline_candidate | **false** |
| allowed_with | dummy_strategy, fixture_config, safe_test_config |
| purpose | Validate lifecycle, artifacts, logs, session_status, simulated reconciliation |
| not_allowed_for | candidate_promotion, strategy_decision, D.3 evidence |

**What this mode proves:**
- Paper session can start and terminate cleanly.
- Artifacts are written to expected paths.
- Logs are recoverable.
- Simulated reconciliation runs without errors.
- Session status is observable throughout.

**What this mode does NOT prove:**
- That any strategy has merit.
- That paper is equivalent to live readiness.
- That evidence from this session can support D.3.

---

### paper_strategy_trial

| Field | Value |
|-------|-------|
| requires_research_pass | **true** |
| requires_baseline_candidate | **true** |
| requires_candidate_memo | **true** |
| requires_stop_conditions | **true** |
| purpose | Validate strategy behavior in paper, validate operator control, validate artifact integrity |
| opens | D.3 review eligibility (not D.3 auto-approval) |

**Entry requirements (all must be true):**
- `robustness_verdict: pass` from at least one confirmatory run
- `baseline_candidate` declared in decision matrix
- `candidate_memo` approved
- `stop_conditions` defined and documented
- `paper_infrastructure_smoke` completed (infrastructure confirmed)
- `before_paper_execution` checklist passed

---

## Comparison Table

| Property | infrastructure_smoke | strategy_trial |
|----------|---------------------|----------------|
| Research pass required | No | Yes |
| Baseline candidate required | No | Yes |
| Candidate memo required | No | Yes |
| Stop conditions required | No | Yes |
| Can use dummy strategy | Yes | No |
| Can contribute to D.3 evidence | No | Yes |
| Can promote candidate | No | No (separate gate) |

---

## Before Paper Execution Checklist

This checklist applies to **paper_strategy_trial** only. Infrastructure smoke
does not require it.

- [ ] `baseline_candidate_exists: true` — Decision matrix confirms baseline candidate
- [ ] `candidate_memo_approved: true` — Memo reviewed and accepted
- [ ] `paper_infrastructure_smoke_passed: true` — Infrastructure confirmed separately
- [ ] `expected_behavior_defined: true` — Entry/exit/hold behavior documented
- [ ] `stop_conditions_defined: true` — Session stop conditions documented (see below)
- [ ] `operator_can_follow_runbook: true` — Operator has read and can execute runbook
- [ ] `artifacts_expected_are_defined: true` — Expected artifacts listed before session
- [ ] `config_hash_locked: true` — Config file frozen and hash recorded

---

## Stop Conditions

Stop conditions must be defined before a paper strategy trial begins.
They are not adjusted after seeing results.

### Hard stops (session must end immediately)

- Any execution error that cannot be attributed to infrastructure
- Drawdown exceeds predefined tolerance band
- Session enters an unobservable state
- Artifact writes fail silently

### Soft stops (operator review required before continuing)

- Turnover materially higher than expected
- Entry/exit pattern diverges from strategy expectation
- Reconciliation discrepancy detected

---

## Operator Readiness

Operator readiness is not a certification. It is a demonstrated state.

An operator is considered ready for paper strategy trial when they can:

- Explain the current session state
- Identify the stop conditions that apply
- Execute a clean session stop according to the runbook
- Locate and open canonical artifacts (`report.json`, `robustness_verdict.json`)
- Identify an ambiguous or unexpected state and escalate

The term "certified" is not used. Readiness is demonstrated through the
before_paper_execution checklist and runbook execution.

---

## paper_infrastructure_smoke vs paper_strategy_trial — Decision Summary

```
paper session requested
        │
        ├─ strategy_trial? ──► baseline_candidate? ──► No ──► BLOCKED
        │                              │
        │                             Yes
        │                              │
        │                      before_paper checklist
        │                              │
        │                      proceed if all pass
        │
        └─ infrastructure_smoke? ──► No research pass needed
                                     ──► dummy_strategy / fixture_config
                                     ──► does NOT contribute to D.3
```

---

## Explicit Exclusions

- Paper does not mean live. A successful paper trial does not authorize live execution.
- Paper success opens D.3 review eligibility, not D.3 auto-approval.
- Broker submit is out of scope for both modes.
- Distributed sweeps are out of scope for both modes.
- Stage E remains blocked regardless of paper outcome.
