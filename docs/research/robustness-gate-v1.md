# Walk-forward Robustness Gate v1

## Purpose

The Walk-forward Robustness Gate evaluates whether a research hypothesis
holds across multiple out-of-sample (OOS) time windows, producing a verdict
artifact that operators and the Desktop can read without re-running or
re-computing anything.

The gate answers one narrow question:

> Is the walk-forward evidence statistically robust enough to warrant
> continued research attention?

A `pass` verdict is **not** an authorization to promote to paper trading,
broker execution, live execution, automation, or capital deployment.

---

## Input artifacts

| Artifact | Required | Description |
|----------|----------|-------------|
| `walkforward_summary.csv` | Yes | Per-split OOS summary with `split_name`, `avg_test_return_topk`, `avg_test_sharpe_topk` |
| `oos_leaderboard.csv` | No | Per-config OOS leaderboard; used to count total OOS trades |

Both artifacts are written by the QuantLab walk-forward runner to the run
output directory at `outputs/runs/<run_id>/`.

---

## Output artifacts

| Artifact | Description |
|----------|-------------|
| `robustness_verdict.json` | Machine-readable verdict (schema v1.0) |
| `robustness_verdict.md` | Human-readable narrative verdict |

Both artifacts are written to the same run output directory. They are
optional — only walk-forward runs emit them. Their absence does not
indicate failure; it means the run type does not produce a verdict.

### `robustness_verdict.json` schema (v1.0)

```json
{
  "artifact_type": "quantlab.walkforward_robustness_verdict",
  "schema_version": "1.0",
  "status": "pass | fail | review",
  "grade": "research_robustness_passed | not_robust | needs_operator_review",
  "total_splits": 3,
  "positive_oos_splits": 2,
  "positive_oos_ratio": 0.667,
  "avg_oos_return_topk": 0.042,
  "avg_oos_sharpe_topk": 0.81,
  "worst_oos_split_return": -0.031,
  "best_oos_split_return": 0.112,
  "total_oos_trades": 47,
  "trade_count_source": "trade_trades",
  "source_artifacts": ["walkforward_summary.csv", "oos_leaderboard.csv"],
  "reasons": ["..."],
  "recommendation": "..."
}
```

---

## Status meanings

### `pass` — `research_robustness_passed`

All hard-fail conditions are absent and no review flags are raised.

The hypothesis showed positive OOS returns across the majority of
evaluated splits, with sufficient trade count, positive average Sharpe,
and no catastrophic worst-split result.

**Recommendation text:** *"Research robustness gate passed. This does not
authorize paper, broker, live, or capital deployment."*

### `fail` — `not_robust`

One or more hard-fail conditions are met.

**Recommendation text:** *"Do not promote to baseline, paper trading,
broker execution, live execution, or capital deployment. Treat as
regime-specific or insufficiently robust research evidence."*

### `review` — `needs_operator_review`

No hard-fail conditions, but one or more review flags are present.
The evidence exists but is incomplete or borderline.

**Recommendation text:** *"Do not promote automatically. Review the
walk-forward evidence and collect stronger OOS evidence before any
baseline, paper, broker, live, or capital-deployment promotion."*

---

## Hard-fail conditions (→ `fail`)

Any single condition triggers `fail`:

| Condition | Threshold | Reason |
|-----------|-----------|--------|
| Positive OOS ratio below threshold | `positive_oos_ratio < 0.66` | Fewer than 66% of OOS splits had positive average test return |
| Worst OOS split catastrophic | `worst_oos_split_return < -0.25` | Worst split return below −25% hard-fail floor |

---

## Review conditions (→ `review` if no hard-fail)

Any single condition triggers `review`:

| Condition | Threshold | Reason |
|-----------|-----------|--------|
| Too few splits | `total_splits < 3` | Fewer than 3 OOS splits provide limited temporal coverage |
| Average OOS return not positive | `avg_oos_return_topk ≤ 0` | Top-k average across splits is not positive |
| Average OOS Sharpe not positive | `avg_oos_sharpe_topk ≤ 0` | Top-k average Sharpe is not positive |
| Insufficient OOS trades | `total_oos_trades < 10` | Fewer than 10 OOS trades; statistical signal unreliable |
| OOS trades unavailable | `oos_leaderboard.csv` absent or unreadable | Cannot confirm trade activity |

There is also a diagnostic (does not change status alone):

- **Concentrated evidence**: positive results from a single OOS split
  when multiple splits exist — included in `reasons` as a warning.

---

## Promotion boundary

**A `pass` verdict authorizes nothing beyond research validation.**

| Action | Authorized by `pass`? |
|--------|----------------------|
| Continue research iteration | Yes |
| Candidate / shortlist tagging in Desktop | Yes — operator decision |
| Promote to baseline | No — requires separate operator review |
| Start paper trading session | No — requires D.3 hardening criteria |
| Broker / live execution | No — requires full execution gate |
| Capital deployment | No — requires full execution gate |
| Automation | No — requires full execution gate |

A `fail` or `review` verdict **blocks promotion recommendation** in the
verdict text, but does not disable any Desktop UI buttons. Promotion
decisions remain with the operator.

---

## How Desktop consumes verdicts

The Desktop reads `robustness_verdict.json` from the local run path via
IPC (`readProjectJson`). It consumes the artifact as-is — it does not
recalculate, re-interpret, or override any field.

Display rules:
- `status` drives the headline color (`pass` → green, `fail` → red, `review` → amber)
- `grade` is shown as a secondary chip
- `recommendation` is displayed prominently as the first actionable text block
- `reasons` are shown as a compact secondary list
- Key metrics (`positive_oos_splits`, `positive_oos_ratio`, `worst_oos_split_return`, `total_oos_trades`) are shown as a metric block
- Missing verdict on a walk-forward run is shown as a neutral "No verdict available" state — not an error

---

## Triggering verdict generation

### Automatic (walk-forward runs)

Walk-forward runs emit `robustness_verdict.json` and `robustness_verdict.md`
automatically after the sweep completes. No manual step is required.

### Manual backfill

For existing walk-forward run directories that predate automatic emission:

```bash
PYTHONPATH=src python main.py --evaluate-walkforward-robustness <run_dir>
```

This writes (or overwrites) `robustness_verdict.json` and
`robustness_verdict.md` in the specified run directory.

---

## Known limitations

- **v1 thresholds are initial values** — `positive_oos_ratio ≥ 0.66`,
  `worst_oos_split_return ≥ −0.25`, `total_splits ≥ 3`, and
  `total_oos_trades ≥ 10` are conservative starting points.
  They have not been calibrated against a broad strategy universe.

- **`review` is not a soft pass** — it means the evidence is incomplete
  or borderline, not that the verdict leans toward pass.

- **Single-split configurations always trigger `review`** — the gate
  requires at least 3 splits to reach `pass`.

- **Trade count uses best-effort extraction** — if `oos_leaderboard.csv`
  is absent or lacks expected columns, trade count is `null` and a
  `review` flag is raised. This is expected for some run configurations.

- **No time-series autocorrelation correction** — the gate treats OOS
  splits as independent. Adjacent splits may share correlated market
  regimes.
