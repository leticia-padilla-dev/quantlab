# Robustness Sweep Matrix v1

This document records the results of running the official config set v1
through the walk-forward robustness gate. Each row is populated after a
run completes and produces `robustness_verdict.json`.

No config is promoted based on this matrix alone. A PASS verdict opens
candidate shortlist review — it does not constitute promotion.

---

## Prerequisites

- [x] Official config set v1 merged (#629)
- [x] Benchmark gate defined (#630)
- [ ] Configs executed — rows pending

---

## Results Matrix

| Config ID | Config File | Asset | Verdict | Positive OOS | Worst Split | Avg OOS Sharpe | Total Trades | Benchmark | Decision | Run ID | Notes |
|-----------|-------------|-------|---------|--------------|-------------|----------------|--------------|-----------|----------|--------|-------|
| C001 | eth_2021_2024_rsi_cooldown_walkforward.yaml | ETH | pending | — | — | — | — | pending | REVIEW | — | Awaiting run |
| C002 | btc_2021_2024_rsi_cooldown_walkforward.yaml | BTC | pending | — | — | — | — | pending | REVIEW | — | Awaiting run |
| C003 | btc_eth_simple_momentum_baseline_walkforward.yaml | ETH | pending | — | — | — | — | self | REVIEW | — | Benchmark peer — not a promotion candidate |

---

## How to Fill a Row

After a walk-forward run completes:

1. Locate `outputs/runs/<run_id>/robustness_verdict.json`
2. Extract: `status`, `positive_oos_splits`, `worst_oos_split_return`,
   `avg_oos_sharpe_topk`, `total_oos_trades`
3. Populate the row and set `Run ID` to the `run_id`
4. Set `Verdict` to `pass` / `fail` / `review`
5. Run benchmark comparison (see `docs/research/benchmark-gate-v1.md`)
6. Set `Benchmark` column per benchmark gate rules
7. Record operator `Decision` in config-decision-matrix.md

Do not change `Decision` in config-decision-matrix.md without completing
the benchmark comparison first.

---

## Failure Taxonomy (for reference when filling rows)

Used to classify FAIL rows before creating variants. See #632 for full taxonomy.

| Type | Symptom |
|------|---------|
| low_split_quality | positive_oos_splits < 2/3 of total splits |
| catastrophic_split | worst_oos_split_return < -25% |
| low_trade_count | total_oos_trades below review floor |
| negative_avg_sharpe | avg_oos_sharpe_topk ≤ 0 |
| concentrated_evidence | only one split sustains the result |
| benchmark_failure | does not beat HODL or no-trade baseline |

---

## PASS Handling

A `pass` verdict does not automatically promote a config. After recording a PASS:

1. Run benchmark comparison (all four B01–B04 peers)
2. Record result in `Benchmark` column
3. If benchmark passes, open candidate shortlist review (#635)
4. Candidate shortlist review requires candidate memo and operator decision
5. Only after shortlist approval does a config move to `baseline_candidate`

---

## FAIL Handling

After recording a FAIL:

1. Classify the failure type using the taxonomy above
2. Record the cause in the `Notes` column
3. Update `Decision` in config-decision-matrix.md to `FAIL`
4. Decide: `archive` / `controlled_variant` (max 2–3 variants, see #634) / no action
5. Document the decision in the `Memo` column of config-decision-matrix.md

---

## Summary (filled after all rows complete)

| Metric | Value |
|--------|-------|
| Configs run | — |
| PASS count | — |
| FAIL count | — |
| REVIEW count | — |
| Benchmark warnings | — |
| Benchmark blocks | — |
| Configs forwarded to shortlist review | — |
