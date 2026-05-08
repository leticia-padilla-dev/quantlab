# Controlled Variants v1

## Purpose

Variants may only be created when a specific failure has a specific,
documented improvement path. This document defines the rules for controlled
variant creation after the failure taxonomy review (#632).

Creating variants without documented reason is prohibited. Brute-force
exploration masquerading as variants defeats the purpose of the robustness gate.

---

## Trigger

This document applies only after:

- Sweep matrix (#631) has been completed
- Failure taxonomy (#632) has been applied to each FAIL config
- At least one failure has a classified cause with a plausible, named fix

Do not create variants speculatively or before failure classification.

---

## Variant Rules

| Rule | Detail |
|------|--------|
| Maximum variants per family | 2–3 |
| `reason` field | Required — names the specific failure cause being addressed |
| `expected_improvement` field | Required — states what should improve (not "see what happens") |
| Gate thresholds | Frozen — variants may not change the robustness gate |
| Config hash | New hash for each variant — confirmatory run required |
| OOS splits | Same splits as the parent config — no redefinition |

A variant that does not declare a `reason` and `expected_improvement` before
running is not a controlled variant. It is undocumented exploration and its
results may not be used for promotion.

---

## Variant Registration Format

Before creating the YAML, register the variant in `config-decision-matrix.md`:

| Field | Example |
|-------|---------|
| Config ID | C004 (next available ID) |
| Hypothesis ID | H001 (same as parent) |
| Config File | eth_2021_2024_rsi_cooldown_v2_volfilter.yaml |
| Decision | REVIEW (initial state) |
| Memo | `variant_of:C001 reason:catastrophic_split_high_vol expected:reduce worst split without degrading others` |

---

## Valid Variant Examples

| Base Config | Failure Type | Named Change | Expected Improvement |
|-------------|--------------|--------------|----------------------|
| C001 (ETH RSI cooldown) | catastrophic_split | Add volatility filter: skip signal when ATR > 2x median | Reduce worst split loss without degrading other splits |
| C002 (BTC RSI cooldown) | low_trade_count | Relax `min_trade_trades` from 3 to 2 | Increase trade count in low-activity splits |
| C001 | concentrated_evidence | Extend cooldown to 7 days | Reduce overfit signal concentration in single regime |

---

## Invalid Variant Examples

| Proposed Change | Why Invalid |
|----------------|-------------|
| "Try RSI 45/65 instead of 50/70" | No specific failure cause named |
| "Run on 2020-2024 instead of 2021-2024" | OOS redefinition, not a variant |
| "Change fee from 0.002 to 0.001" | Not addressing a classified failure |
| "Add more param combinations" | Brute force expansion |

---

## What Happens After a Second FAIL

If a variant also fails the robustness gate:

1. Classify the failure type (same taxonomy as parent)
2. Check: is there new diagnostic information that was not available before?
3. If yes: one more variant may be justified if reason and expected improvement are documented
4. If no: the hypothesis family should be archived

A second FAIL with no new diagnostic information → `archive`.
No third variant without extraordinary documented justification.

---

## Variant Lifecycle in Decision Matrix

```
parent fails gate
    │
    └── failure classified (#632)
            │
            ├── archive decision → no variant created
            │
            └── controlled_variant decision
                    │
                    ├── register in decision matrix (Decision = REVIEW)
                    ├── create YAML with reason + expected_improvement
                    ├── lock config_hash before confirmatory run
                    ├── run → verdict
                    │
                    ├── PASS → shortlist review (#635)
                    └── FAIL → classify → archive or 1 more variant (if new info)
```

---

## Variant Config Header Template

Add these fields to the top of each variant YAML:

```yaml
# Controlled variant of <parent_config_id>.
# variant_of: <parent config ID, e.g. C001>
# hypothesis_id: <same as parent>
# config_id: <new ID, e.g. C004>
# failure_addressed: <failure type from taxonomy>
# reason: <specific cause being addressed>
# expected_improvement: <what should change and in which direction>
# gate_thresholds: unchanged
```
