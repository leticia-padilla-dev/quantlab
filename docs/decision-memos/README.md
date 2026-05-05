# QuantLab Decision Memos

This directory stores **Trading Decision Memos**. A memo is a structured decision card, not a long analysis or a prediction. It documents what idea you have, what evidence exists, what risk you see, and what decision you make.

## File Format

Memos should be named using the format: `YYYY-MM-DD-asset-verdict.md`

Examples:
- `2026-05-05-eth-observe.md`
- `2026-05-06-btc-no-trade.md`
- `2026-05-07-eth-paper-only.md`

## Allowed Verdicts

Memos must strictly use one of these verdicts:

- `no_trade`: QuantLab evidence is bad/weak, or risk is undefined.
- `observe`: Interesting idea, but no QuantLab evidence exists yet. Not ready for paper.
- `paper_only`: QuantLab evidence is strong enough to test without capital risk.
- `candidate_for_future_supervised_live_review`: Paper evidence is strong enough to consider a future supervised review. **(This does NOT open Stage E)**.

## Core Rules

1. **8 Mandatory Sections**: Every memo must contain: Metadata, Market idea, Hypothesis, QuantLab evidence, Metrics reviewed, Risk review, Decision, and Boundaries.
2. **Evidence Gate**: If there is no QuantLab evidence, the memo can ONLY be `observe` or `no_trade`.
3. **Paper Gate**: You cannot use `paper_only` without prior QuantLab backtest/sweep evidence.
4. **Live Gate**: You cannot use `candidate_for_future_supervised_live_review` without strong paper evidence.
