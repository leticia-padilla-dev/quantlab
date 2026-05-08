# Config Decision Matrix

Each config that enters the research pipeline must have a row in this matrix.
No config may be promoted to candidate without a row and a recorded decision.

## Decision States

| State | Meaning |
|-------|---------|
| FAIL | Robustness gate failed — not promoted |
| REVIEW | Gate not run or result ambiguous — operator review required |
| PASS | Robustness gate passed — eligible for shortlist review |
| ARCHIVED | No further iteration warranted — documented reason required |

## Matrix

| Config ID | Hypothesis ID | Config File | Asset | Window | Splits | Verdict | Positive OOS | Worst Split | Trades | Benchmark | Decision | Memo |
|-----------|---------------|-------------|-------|--------|--------|---------|--------------|-------------|--------|-----------|----------|------|
| C001 | H001 | eth_2021_2024_rsi_cooldown_walkforward.yaml | ETH | 2021–2024 | — | — | — | — | — | pending | REVIEW | Pending first run |
| C002 | H002 | btc_2021_2024_rsi_cooldown_walkforward.yaml | BTC | 2021–2024 | — | — | — | — | — | pending | REVIEW | Pending first run |
| C003 | H003 | btc_eth_simple_momentum_baseline_walkforward.yaml | BTC/ETH | 2021–2024 | — | — | — | — | — | self | REVIEW | Benchmark peer |

## Column Definitions

| Column | Description |
|--------|-------------|
| Config ID | Unique config identifier (C001, C002, …) |
| Hypothesis ID | Hypothesis this config tests (from hypothesis-registry.md) |
| Config File | YAML file path under `configs/` |
| Asset | Primary asset(s) |
| Window | Training + OOS date range |
| Splits | Number of OOS walk-forward splits |
| Verdict | `pass` / `fail` / `review` from `robustness_verdict.json` |
| Positive OOS | Count of OOS splits with positive return |
| Worst Split | Worst OOS split return |
| Trades | Total OOS trades |
| Benchmark | Benchmark peer comparison result |
| Decision | Operator decision: FAIL / REVIEW / PASS / ARCHIVED |
| Memo | One-line rationale for the decision |

## Rules

- A PASS verdict does not automatically set Decision = PASS. Operator must record the decision.
- A Decision = ARCHIVED requires a documented reason in the Memo column.
- Benchmark column must reference at least HODL and no-trade before a config can reach shortlist.
- Config hash must be locked before a config transitions from REVIEW to PASS.
- No config may have Decision = PASS without a `robustness_verdict.json` artifact.

## Benchmark Peers Required Before Shortlist

| Peer | Description |
|------|-------------|
| no_trade_or_cash | Zero-activity baseline (opportunity cost floor) |
| buy_and_hold_asset | HODL the primary asset |
| simple_momentum_or_rsi_baseline | Weak systematic baseline |
| previous_baseline_if_exists | Prior shortlisted config, if any |
