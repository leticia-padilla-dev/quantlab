# Benchmark Gate v1

## Purpose

A positive walk-forward result does not establish merit unless it beats
simple alternatives. The Benchmark Gate defines required peer strategies
that every candidate config must be compared against before it can reach
the candidate shortlist.

A config that does not outperform required benchmarks on a risk-adjusted
basis is blocked from shortlist promotion — unless the operator provides
explicit documented justification.

---

## Required Benchmark Peers

All four peers must appear in the benchmark comparison before a config
can transition from PASS to shortlist review.

| Peer ID | Name | Description |
|---------|------|-------------|
| B01 | no_trade_or_cash | Zero-activity baseline — represents the opportunity cost of holding cash. A strategy that does not beat doing nothing has no merit. |
| B02 | buy_and_hold_asset | HODL the primary asset for the full OOS window. Establishes the passive return available without any signal. |
| B03 | simple_momentum_or_rsi_baseline | Weak systematic rule (e.g. H003 config). A candidate must justify added complexity over a naive system. |
| B04 | previous_baseline_if_exists | The prior shortlisted config, if any exists. Prevents regression disguised as improvement. |

---

## Benchmark Decision Rule

The operator reviews benchmark comparison after the robustness gate passes.

### Blocking condition

A config is **blocked from shortlist promotion** if it:

- Underperforms `buy_and_hold_asset` (B02) on a risk-adjusted basis AND
- The operator cannot provide documented justification (e.g. lower drawdown,
  better Sharpe, regime-specific merit)

### Warning condition

A config receives a **benchmark warning** if it:

- Underperforms `no_trade_or_cash` (B01) in any OOS split
- Underperforms `simple_momentum_or_rsi_baseline` (B03) on average OOS Sharpe
- Would represent a regression from `previous_baseline_if_exists` (B04)

A warning does not auto-block but requires operator annotation in the
decision matrix Memo column before shortlist can proceed.

### Pass condition

A config may proceed to shortlist review if:

- It outperforms all required peers on risk-adjusted basis, OR
- It underperforms one peer with documented operator justification that
  identifies a compensating merit (e.g. lower max drawdown, better tail behavior)

---

## Benchmark Calculation Requirements

Each benchmark peer must be calculated over the **same OOS splits** as the
candidate config. Cross-split benchmark comparison is not valid.

| Benchmark | Calculation |
|-----------|-------------|
| no_trade_or_cash | 0% return every OOS split (opportunity cost floor) |
| buy_and_hold_asset | Buy at start of each OOS split, sell at end |
| simple_momentum_or_rsi_baseline | Run H003 config over same splits |
| previous_baseline_if_exists | Use recorded shortlist results from prior review cycle |

---

## Integration with Config Decision Matrix

The `Benchmark` column in `docs/research/config-decision-matrix.md` must
be populated before a config's Decision can change from REVIEW to PASS.

Valid values for the Benchmark column:

| Value | Meaning |
|-------|---------|
| `pending` | Benchmark comparison not yet run |
| `pass` | Outperforms all required peers (or justified exceptions) |
| `warn:B01` | Warning: underperforms no_trade baseline |
| `warn:B02` | Warning: underperforms HODL |
| `warn:B03` | Warning: underperforms simple baseline |
| `blocked` | Blocked from shortlist — benchmark failure with no justification |

---

## What This Gate Does NOT Do

- It does not change the robustness gate thresholds.
- It does not replace the robustness verdict (`robustness_verdict.json`).
- It does not authorize paper trading, live execution, or capital deployment.
- A benchmark PASS does not constitute a shortlist decision — it only removes
  one blocker. Shortlist review still requires candidate memo and operator decision.

---

## Exit Condition

This gate is satisfied when:

- All four benchmark peers are calculated over the same OOS splits
- The `Benchmark` column in the decision matrix is populated (not `pending`)
- Any `warn:` entries have an operator annotation in the `Memo` column
- No `blocked` config proceeds to shortlist without a superseding operator decision
