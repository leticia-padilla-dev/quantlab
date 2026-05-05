# Trading Decision Memo — ETH Observe

## Metadata

```yaml
decision_id: 2026-05-05-eth-001
date: 2026-05-05
operator: marce
asset: ETH
verdict: observe
stage_boundary: Stage E blocked
```

## 1. Market idea

ETH may be showing short-term continuation potential, but the idea is not yet backed by QuantLab evidence.

This memo records the idea as an observation only. It is not a trading signal, not a paper-trading authorization, and not a live-execution authorization.

## 2. Hypothesis

```yaml
hypothesis:
  direction: long
  horizon: 1d-3d
  thesis: "ETH may continue upward if recent momentum persists and downside volatility remains controlled."
  invalidation_condition: "ETH loses recent short-term support, volatility expands sharply, or BTC/market context weakens."
```

## 3. QuantLab evidence

```yaml
quantlab_evidence:
  run_ids: []
  sweep_ids: []
  paper_session_ids: []
  artifacts_reviewed: []
```

No QuantLab run, sweep, or paper session has been executed for this idea yet.

## 4. Metrics reviewed

```yaml
key_metrics:
  return: null
  sharpe: null
  max_drawdown: null
  win_rate: null
  expectancy: null
  fees_impact: null
  notes: "No metrics available yet. This is an observation memo."
```

## 5. Risk review

```yaml
risk_review:
  max_loss_if_wrong: "not_defined"
  position_size_plan: "none"
  leverage_allowed: false
  stop_condition: "not_defined"
  uncertainty: "high"
```

## 6. Decision

```yaml
decision:
  status: observe
  reason: "The idea is interesting but has no QuantLab evidence yet. It is not eligible for paper trading or supervised live review."
```

## 7. Next action

```yaml
follow_up:
  next_action: "Run a QuantLab research test for ETH short-term momentum continuation."
  review_after: "after first QuantLab run or sweep is available"
```

## 8. Boundaries

```yaml
boundaries:
  live_execution: false
  stage_e_open: false
  broker_submit_allowed: false
  automation_allowed: false
```

## Revision 1 — QuantLab evidence review

```yaml
revision:
  date: 2026-05-05
  reason: "First QuantLab evidence pass for ETH short-term momentum continuation."
  evidence_source: "existing_artifacts_reviewed_no_new_sweep"
  sweep_config: configs/experiments/eth_2023_walkforward.yaml
  reviewed_run_ids:
    - 20260504_140139_walkforward_95ae2e9
    - 20260505_100323_walkforward_95ae2e9
  primary_run_id: 20260505_100323_walkforward_95ae2e9
  artifacts_reviewed:
    - outputs/runs/20260505_100323_walkforward_95ae2e9/report.json
    - outputs/runs/20260505_100323_walkforward_95ae2e9/metrics.json
    - outputs/runs/20260505_100323_walkforward_95ae2e9/run_report.md
    - outputs/runs/20260505_100323_walkforward_95ae2e9/walkforward_summary.csv
    - outputs/runs/20260505_100323_walkforward_95ae2e9/oos_leaderboard.csv
  key_metrics:
    mode: walkforward
    ticker: ETH-USD
    train_window: 2023-01-01_to_2023-07-01
    test_window: 2023-07-01_to_2024-01-01
    total_return: 0.3145084585
    sharpe_simple: 3.4112878580
    max_drawdown: -0.0251578196
    trades: 2
    trade_trades: 1
    win_rate_trades: 1.0
    avg_holding_days: 20.0
    n_train_runs: 27
    n_selected: 3
    n_test_runs: 3
  evidence_summary:
    result: "Existing walkforward evidence is strong enough to justify paper-only validation."
    strengths:
      - "Out-of-sample test return was positive at approximately 31.45%."
      - "Out-of-sample drawdown was limited at approximately -2.52%."
      - "The best selected test configuration produced Sharpe above 3.4."
      - "Canonical artifacts are present and reproducible from the configured walkforward sweep."
    weaknesses:
      - "Only 2 OOS trades were generated, with effectively 1 round trip, so sample size is too small for live confidence."
      - "The train window best metrics were weak while the test window was strong, which raises regime-specific uncertainty."
      - "The reviewed runs are duplicate-equivalent outputs from the same walkforward configuration, not independent evidence."
    uncertainty:
      - "Evidence may be sensitive to the 2023 ETH regime."
      - "Paper validation is required before any future supervised-live review."
      - "No broker, live, or automated execution is authorized by this memo."
  previous_verdict: observe
  verdict_after_review: paper_only
  decision_reason: "Promote from observe to paper_only because existing QuantLab walkforward evidence is positive and complete, while the very small trade sample blocks any live-review interpretation."
```

Revision 1 does not open Stage E, does not authorize broker submission, and does not authorize automation. The only approved next step is paper validation under the existing QuantLab decision workflow.
