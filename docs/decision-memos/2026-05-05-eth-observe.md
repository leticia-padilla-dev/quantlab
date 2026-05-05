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

## Revision 2 — Paper validation review

```yaml
revision:
  date: 2026-05-05
  reason: "First controlled paper validation for ETH momentum continuation."
  paper_session_id: 20260505_205127_paper_ddc7c3f
  paper_session_path: outputs/paper_sessions/20260505_205127_paper_ddc7c3f
  validation_mode: paper_only
  initial_cash: 10000
  window: 2023-07-01_to_2024-01-01
  operator_command_recorded: "python main.py --ticker ETH-USD --start 2023-07-01 --end 2024-01-01 --paper --report --initial_cash 10000"
  artifact_reproduce_command: "python main.py --sweep inline_cli --sweep_outdir C:\\dev\\quantlab\\outputs\\paper_sessions"
  artifacts_generated:
    - outputs/paper_sessions/20260505_205127_paper_ddc7c3f/report.json
    - outputs/paper_sessions/20260505_205127_paper_ddc7c3f/run_report.md
    - outputs/paper_sessions/20260505_205127_paper_ddc7c3f/metrics.json
    - outputs/paper_sessions/20260505_205127_paper_ddc7c3f/session_status.json
    - outputs/paper_sessions/20260505_205127_paper_ddc7c3f/trades.csv
    - outputs/paper_sessions/20260505_205127_paper_ddc7c3f/artifacts/equity.png
  paper_metrics:
    total_return: 0.1176463283
    total_return_pct: 11.76
    max_drawdown: -0.0236252740
    max_drawdown_pct: -2.36
    sharpe_simple: 2.6292727151
    win_rate_trades: 0.5
    profit_factor: 5.3609753994
    expectancy_net: 588.3034439039
    exposure: 0.1940298507
    avg_holding_days: 6.5
    days: 85
    trades: 4
    trade_trades: 2
  paper_health:
    state: success
    status_reason: completed
    terminal: true
    duration_seconds: 1.319843
    alert_status: not_recorded_in_paper_artifacts
  evidence_summary:
    result: "Paper validation completed successfully with positive return, controlled drawdown, and complete core paper artifacts."
    strengths:
      - "Paper session completed successfully."
      - "Return was positive at approximately 11.76%."
      - "Max drawdown remained limited at approximately -2.36%."
      - "Sharpe remained positive at approximately 2.63."
      - "The session generated canonical paper artifacts including report, metrics, status, and trades."
    weaknesses:
      - "The validation uses a historical OOS window, not live forward time."
      - "The run is still paper-only and does not authorize live execution."
      - "Only 2 round-trip trades were present, so live-review confidence remains limited."
      - "Further forward/paper validation is needed before any supervised-live candidate review."
    uncertainty:
      - "Results may remain regime-specific to the 2023 ETH window."
      - "No real-time market execution behavior has been tested."
      - "Stage E remains blocked."
  previous_verdict: paper_only
  verdict_after_paper: paper_only
  decision_reason: "Keep as paper_only because the controlled paper validation is positive, but it is still not enough to justify supervised-live review."
```

Revision 2 does not open Stage E, does not authorize broker submission, and does not authorize automation. The setup remains paper-only pending further forward/paper validation.
