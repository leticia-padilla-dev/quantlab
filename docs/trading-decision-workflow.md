# Trading Decision Workflow

## Status

QuantLab may be used as a trading decision laboratory.

QuantLab must not be used as:
- an automated trading system
- a Stage E live execution system
- a signal-to-order engine

Stage E remains blocked.

---

## 1. Purpose

This workflow turns a market idea into a documented trading decision using QuantLab evidence.

The goal is not to predict perfectly.
The goal is to reduce impulsive decisions and make every decision auditable.

---

## 2. Decision Flow

```text
Market idea
→ hypothesis
→ research run / sweep
→ evidence review
→ paper session
→ operator verdict
```

---

## 3. Allowed Verdicts

### no_trade

Use when evidence is weak, contradictory, or risk is unclear.

### observe

Use when the idea is interesting but not ready for paper.

### paper_only

Use when the idea is strong enough to test without capital risk.

### candidate_for_future_supervised_live_review

Use only when paper evidence is strong enough to consider a future supervised review.

This does not open Stage E.

---

## 4. Trading Decision Memo Template

```yaml
trading_decision:
  decision_id:
  date:
  operator: marce

  market_context:
    asset:
    timeframe:
    source_of_idea:
    summary:

  hypothesis:
    direction:
    horizon:
    thesis:
    invalidation_condition:

  quantlab_evidence:
    run_ids:
    sweep_ids:
    paper_session_ids:
    artifacts_reviewed:
      - report.json
      - metrics.json
      - session_status.json

  key_metrics:
    return:
    sharpe:
    max_drawdown:
    win_rate:
    expectancy:
    fees_impact:
    notes:

  risk_review:
    max_loss_if_wrong:
    position_size_plan:
    leverage_allowed: false
    stop_condition:
    uncertainty:

  verdict:
    status:
    allowed_values:
      - no_trade
      - observe
      - paper_only
      - candidate_for_future_supervised_live_review
    reason:

  follow_up:
    next_action:
    review_after:
```

---

## 5. Decision Rules

A decision cannot be promoted if:

* no QuantLab artifact exists
* risk is not defined
* invalidation is unclear
* drawdown is unacceptable
* paper evidence is missing
* the operator cannot explain why the trade is valid
* the decision depends only on emotion, urgency, or fear of missing out

---

## 6. Stage Boundary

This workflow may produce a future candidate for supervised live review.

It does not:

* open Stage E
* submit orders
* automate decisions
* bypass D.3 hardening declarations
