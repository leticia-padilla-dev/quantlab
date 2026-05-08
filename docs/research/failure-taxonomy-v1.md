# Failure Taxonomy v1

## Purpose

Understanding why a config fails is required before creating variants.
This document defines the failure taxonomy for walk-forward robustness
results and the operator decisions that follow each failure type.

A config family that does not deserve more iteration must be archived.
Only failure types with documented, plausible improvement paths justify
controlled variants.

---

## Failure Types

| Type | Symptom | Diagnostic |
|------|---------|------------|
| `low_split_quality` | `positive_oos_splits` < 2 of 3 splits | Examine per-split returns in `walkforward_summary.csv` |
| `catastrophic_split` | `worst_oos_split_return` < -25% | Identify which split and what regime it covers |
| `low_trade_count` | `total_oos_trades` < 10 across all OOS splits | Check `min_trade_trades` constraint and param grid size |
| `negative_avg_sharpe` | `avg_oos_sharpe_topk` ≤ 0 | Strategy generates negative risk-adjusted return on average |
| `concentrated_evidence` | Only one OOS split shows positive return | Evidence is not robust across regimes |
| `benchmark_failure` | Does not outperform HODL or no-trade baseline (B01/B02) | Run benchmark comparison per `benchmark-gate-v1.md` |
| `insufficient_data` | Train or OOS window too short to produce stable splits | Review window size vs split count |

---

## Operator Decisions After FAIL

After classifying a failure, the operator must record one of these decisions
in the `config-decision-matrix.md` Memo column:

| Decision | Meaning | Next step |
|----------|---------|-----------|
| `archive` | No further iteration warranted | Close the config family; no variants |
| `controlled_variant` | A specific, documented improvement is plausible | Create max 2–3 variants per #634 rules |
| `no_action` | Failure noted; review cycle continues | Row stays FAIL with note; no action yet |

The default when in doubt is `archive`. Creating variants requires explicit
documented reasoning.

---

## When to Archive a Failure Family

Archive when any of the following apply:

- `negative_avg_sharpe` with no identifiable market regime explanation
- `benchmark_failure` (B01 or B02) with no compensating metric
- `low_split_quality` AND `catastrophic_split` in the same config
- `concentrated_evidence` with no hypothesis for why one regime differs
- The hypothesis itself was poorly formed (lack of clear causal mechanism)

A hypothesis family that is archived may not be re-opened without a new
hypothesis ID and documented reason (see `hypothesis-registry.md`).

---

## When a Controlled Variant Is Justified

A variant is only justified when:

1. The failure has a specific, named cause (e.g. catastrophic split coincides
   with a documented extreme volatility regime)
2. There is a specific, named change that addresses that cause
3. The expected improvement is stated before the variant runs
4. The change does not require modifying the robustness gate thresholds

| Failure type | Example valid variant reason | Example invalid reason |
|--------------|------------------------------|------------------------|
| `catastrophic_split` | Add volatility filter to avoid signal during regime X | "Try different RSI values" |
| `low_trade_count` | Relax `min_trade_trades` constraint | "Run more combinations" |
| `low_split_quality` | Extend training window to capture more regimes | "Maybe it works on other assets" |
| `concentrated_evidence` | Add cooldown to reduce overfit to single regime | "Let's see what happens" |

---

## Variant Rules

From issue #634:

- Maximum 2–3 variants per hypothesis family
- Each variant requires an explicit `reason` field
- Each variant requires an `expected_improvement` field
- Gate thresholds remain frozen

Variants that fail inherit the failure family's FAIL history. A second FAIL
with no new diagnostic information should result in `archive`.

---

## Integration with Config Decision Matrix

After classifying each FAIL row:

1. Set `Decision` to `FAIL` in `config-decision-matrix.md`
2. Add failure type to `Memo` column (e.g. `FAIL:low_split_quality`)
3. Add operator decision (`archive` / `controlled_variant` / `no_action`)
4. If `controlled_variant`: create a new config ID entry in the matrix
   with `Decision = REVIEW` before running

---

## Non-Promotion Gate

A config with any of the following may not proceed to shortlist review:

- `Decision = FAIL` with no superseding operator override
- `Benchmark = blocked` (benchmark gate failure without justification)
- No `robustness_verdict.json` artifact
- No `config_hash` recorded (not confirmatory)

---

## Failure Summary Template

After completing the sweep matrix (#631), fill in:

```
FAIL summary:
  total_fail_configs: <n>
  archived_families: <list>
  controlled_variants_created: <n>
  failure_types_seen: <list>
  notes: <any cross-config observations>
```
