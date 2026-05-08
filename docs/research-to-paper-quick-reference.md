# Research-to-Paper Quick Reference Guide

> **Objective:** A quick reference for the promotion system. 
> Remember: `positive backtest != promotion`, `PASS != paper`, `paper != live`, `D.3 != Stage E`.

## 1. The Golden Rule

```text
A positive backtest promotes nothing.
A robustness PASS opens candidate review.
Candidate review may open baseline_candidate.
Baseline candidate + paper readiness may open supervised paper.
Paper success may open D.3 review.
D.3 repeatable evidence may open Stage E consideration.
Stage E requires a separate explicit decision.
```

## 2. The Two-Lane Model

QuantLab progresses via two independent tracks:
- **Lane A (Research):** Find robust hypotheses.
- **Lane B (Operations):** Mature paper/evidence infrastructure.

*You can improve paper infrastructure without waiting for a PASS. But you cannot execute a paper strategy without a baseline candidate.*

## 3. Core Principle (Forbidden vs Correct)

- **❌ Optimize to pass gate**
- **✅ Build evidence to deserve pass**

QuantLab is not a machine to reach live trading quickly. It is a machine to prevent a hypothesis from reaching live trading without deserving it.

## 4. Promotion States & Opens Table

| State | Opens | Does NOT Open |
|---|---|---|
| `rejected` | archive / lessons learned | review, paper, live |
| `research_review` | analysis memo | paper |
| `robustness_pass` | candidate_review | paper, D.3, live |
| `shortlisted_candidate` | baseline review | paper execution |
| `baseline_candidate` | paper plan | live, D.3 |
| `paper_ready` | supervised paper trial | D.3 automatically |
| `paper_passed` | D.3 readiness review | Stage E |
| `d3_candidate` | bounded micro-live review | unsupervised live |
| `d3_passed_repeatable` | Stage E consideration | automation |
| `live_blocked` | nothing | everything live-facing |

## 5. Promotion Decision Tree

```text
robustness_pass
  ↳ opens candidate_review

candidate_review approved
  ↳ opens baseline_candidate

baseline_candidate
  ↳ opens paper_plan

baseline_candidate + paper_infrastructure_ready
  ↳ opens supervised paper_strategy_trial

paper_passed
  ↳ opens D.3 readiness review

D.3 passed
  ↳ opens Stage E gate discussion
```

## 6. Readiness Checklists

### Before Paper Execution
**Required:**
- [ ] `baseline_candidate` exists
- [ ] candidate memo approved
- [ ] paper infrastructure smoke passed
- [ ] expected behavior defined (including drift tolerance)
- [ ] stop conditions defined
- [ ] operator can follow runbook and identify ambiguity
- [ ] expected artifacts are defined

**Not Required:**
- [ ] profit expectation
- [ ] live readiness
- [ ] broker submit

### Before D.3 (Micro-Live)
**Required:**
- [ ] capital limits defined
- [ ] daily loss limit defined
- [ ] alert artifact requirements met
- [ ] reconciliation requirements met
- [ ] stop-control checklist passed
- [ ] secret-boundary checklist passed

### Before Stage E
**Alert Gate Required:**
- [ ] no missing critical alerts (false negatives are dangerous)
- [ ] critical alerts are actionable
- [ ] false positives reviewed and bounded
- [ ] no alert requires log archaeology
