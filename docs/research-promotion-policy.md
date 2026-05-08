# Research Promotion Policy

## Purpose

This document defines the canonical research promotion policy for QuantLab. Its purpose is to ensure that positive backtests, robustness `PASS`, candidate review, baseline candidates, paper readiness, `D.3`, and `Stage E` remain clearly separated and deliberately gated.

QuantLab does not optimize to achieve a `PASS`. QuantLab builds evidence to deserve promotion.

## Promotion Axiom

A positive backtest is not a promotion. It is only the first piece of evidence required to ask for a promotion.

## Golden Rule

```text
A positive backtest promotes nothing.
A robustness PASS opens candidate review.
Candidate review may open baseline_candidate.
Baseline candidate + paper readiness may open supervised paper.
Paper success may open D.3 review.
D.3 repeatable evidence may open Stage E consideration.
Stage E requires a separate explicit decision.
```

## Promotion States

QuantLab strategies exist in one of the following formally defined states:

1. **`rejected`**: The hypothesis failed validation or review and is archived.
2. **`research_review`**: The strategy has a completed run and is awaiting review.
3. **`robustness_pass`**: The strategy passed the automated robustness gate but has not yet been accepted as a candidate.
4. **`shortlisted_candidate`**: The strategy has passed candidate review and is pending baseline review.
5. **`baseline_candidate`**: The strategy is the current reference point for a given hypothesis family.
6. **`paper_ready`**: The baseline candidate has a paper plan and the paper infrastructure is ready.
7. **`paper_passed`**: The strategy has completed its supervised paper trial successfully.
8. **`d3_candidate`**: The strategy is undergoing a bounded micro-live review.
9. **`d3_passed_repeatable`**: The strategy has proven repeatable evidence in D.3.
10. **`live_blocked`**: The strategy is explicitly blocked from live execution.

## States and Opens Table

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

## Robustness Gate v1

A strategy achieves a `PASS` only if it meets all pre-defined automated criteria in the robustness gate.
- The gate must be evaluated out-of-sample (OOS).
- The gate rules must be defined *before* the run is evaluated.
- Changing gate thresholds after seeing results is strictly forbidden.

## Trade Count Tiers

Evidence quality scales with sample size. Strategies must be evaluated against appropriate trade count tiers:
- **Low**: Insufficient statistical significance (requires manual justification).
- **Medium**: Minimum acceptable tier for candidate review.
- **High**: Preferred tier for baseline candidates.

## Benchmark Requirement

A strategy cannot pass review if it does not beat simple alternatives.
- **Required peers:** `no_trade_or_cash`, `buy_and_hold_asset`, `simple_momentum_or_rsi_baseline`, and the `previous_baseline_if_exists`.
- **Criteria:** The candidate must outperform on a risk-adjusted basis, avoid worse drawdowns unless explicitly justified, and justify any extra complexity.

## Anti-Curve-Fitting Contract

We do not optimize to pass the gate.
- Iterations must be driven by hypothesis, not by score-seeking.
- Excessive iteration on the same dataset invalidates the OOS integrity.
- Any variant must have an explicitly documented `reason` and `expected_improvement`.

## Discovery vs Confirmatory Validation

Research is divided into two distinct modes to protect OOS integrity:
- **Discovery Mode:** Used to learn, detect patterns, and inform variants. Cannot promote directly to a candidate.
- **Confirmatory Mode:** Used to validate a frozen config (`config_hash_locked: true`). This is the only mode used for promotion. OOS splits must be locked.

## Non-Promotion Gate

If a strategy fails to meet the required criteria or lacks sufficient evidence, it triggers the non-promotion gate. The failure must be classified (e.g., `catastrophic_split`, `benchmark_failure`) and documented.

## Research Sunset Criteria

Hypothesis families that repeatedly trigger the non-promotion gate without clear paths to improvement must be archived to prevent infinite iteration and OOS contamination.

## Handoff Boundaries

```yaml
handoff_boundaries:
  robustness_pass:
    opens: candidate_review
    does_not_open:
      - paper
      - D3
      - live

  baseline_candidate:
    opens:
      - paper_plan
    does_not_open:
      - paper_execution_automatic
      - D3
      - live

  paper_ready:
    opens:
      - supervised_paper_trial
    does_not_open:
      - D3_automatic
      - Stage_E
```

## Forbidden vs Correct

- **❌ Optimize to pass gate**
- **✅ Build evidence to deserve pass**

QuantLab is not a machine to reach live trading quickly. It is a machine to prevent a hypothesis from reaching live trading without deserving it.

## Out of Scope

This policy governs the promotion logic up to the decision gates. It does not dictate:
- Execution code or runtime behavior.
- Specific config generation or variant creation.
- The technical implementation of D.2, D.3, or Stage E.
- External systems like Stepbit or the Desktop UI.