# ETH Paper Validation Plan — Momentum Continuation

## Metadata

```yaml
plan_id: 2026-05-05-eth-paper-plan-001
date: 2026-05-05
operator: marce
asset: ETH
mode: paper_validation
linked_decision_memo: docs/decision-memos/2026-05-05-eth-observe.md
current_verdict: paper_only
stage_boundary: Stage E blocked
```

## 1. Purpose

This plan defines a controlled paper validation for the ETH momentum continuation idea.

The purpose is to test whether the `paper_only` verdict remains valid outside the reviewed walkforward evidence.

This plan does not authorize live execution, broker submit, automation, or Stage E.

## 2. Evidence source

```yaml
evidence_source:
  primary_run_id: 20260505_100323_walkforward_95ae2e9
  secondary_run_id: 20260504_140139_walkforward_95ae2e9
  strategy_reference: configs/experiments/eth_2023_walkforward.yaml
  reviewed_artifacts:
    - outputs/runs/20260505_100323_walkforward_95ae2e9/report.json
    - outputs/runs/20260505_100323_walkforward_95ae2e9/metrics.json
    - outputs/runs/20260505_100323_walkforward_95ae2e9/run_report.md
    - outputs/runs/20260505_100323_walkforward_95ae2e9/walkforward_summary.csv
    - outputs/runs/20260505_100323_walkforward_95ae2e9/oos_leaderboard.csv
```

## 3. Hypothesis

```yaml
hypothesis:
  asset: ETH
  direction: long
  horizon: 1d-3d
  thesis: "ETH short-term momentum continuation may remain valid if price behavior stays aligned with the walkforward-selected configuration."
  invalidation_condition: "Momentum weakens, volatility expands beyond the plan, or the setup no longer resembles the reviewed evidence regime."
```

## 4. Paper preconditions

```yaml
paper_preconditions:
  asset: ETH
  direction: long
  horizon: 1d-3d
  strategy_reference: configs/experiments/eth_2023_walkforward.yaml
  primary_evidence_run: 20260505_100323_walkforward_95ae2e9
  max_risk_simulated: "must be written as a concrete percentage or simulated notional before paper entry"
  invalidation_condition: "must be measurable before paper entry"
  expected_holding_period: "approx 3-20 days"
  reference_price_required: true
  entry_timestamp_required: true
  no_real_capital: true
  broker_submit_allowed: false
  live_execution_allowed: false
  automation_allowed: false
```

## 5. Entry logic

Paper entry is allowed only if:

```yaml
entry_logic:
  - ETH still matches the momentum continuation hypothesis
  - risk boundary is defined before entry as a concrete percentage or simulated notional
  - invalidation condition is measurable and written before entry
  - entry timestamp is recorded
  - reference price is recorded
  - no real capital is used
```

If the reference price or timestamp is missing, the paper entry is invalid.

## 6. Exit and invalidation logic

Paper exit or invalidation is triggered if:

```yaml
exit_logic:
  - planned holding window expires
  - invalidation condition triggers
  - volatility expands beyond the paper plan
  - setup no longer resembles the reviewed evidence regime
  - tracking becomes incomplete or ambiguous
```

## 7. Observation cadence

```yaml
observation_cadence:
  first_review: "after 1 day"
  second_review: "after 3 days"
  final_review: "after exit condition or planned holding window"
  required_notes:
    - price behavior
    - drawdown against paper entry
    - whether thesis still holds
    - whether invalidation triggered
```

## 8. Success criteria

```yaml
success_criteria:
  - thesis remains valid through the review window
  - downside remains inside predefined invalidation/risk boundary
  - paper tracking is complete
  - operator can explain why the setup remains valid
  - no live execution or broker submit occurred
```

## 9. Failure criteria

```yaml
failure_criteria:
  - invalidation triggers
  - volatility expands beyond the plan
  - signal disappears
  - paper tracking is incomplete
  - decision depends on discretion or emotion instead of evidence
```

## 10. Review path

At the end of paper validation, update the original memo:

```text
docs/decision-memos/2026-05-05-eth-observe.md
```

Add:

```text
Revision 2 — Paper validation review
```

Allowed next verdicts:

```yaml
allowed_next_verdicts:
  - no_trade
  - observe
  - paper_only
  - candidate_for_future_supervised_live_review
```

`candidate_for_future_supervised_live_review` is allowed only if paper evidence is strong and complete. It still does not open Stage E.

Revision 2 records the outcome only after paper tracking is complete.

## 11. Boundaries

```yaml
boundaries:
  live_execution: false
  broker_submit_allowed: false
  stage_e_open: false
  automation_allowed: false
  stepbit_integration: false
```
