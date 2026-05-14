# D3 #751 — invalid_size Rejection Analysis (report-only)

analysis_only: true
submit_allowed: false
runtime_changes: false
stage_e: blocked

## Context

Issue #749 produced a supervised single-submit attempt that was rejected remotely with:

- `status_error:Order has invalid size.`

This document is analysis-only. It classifies a likely root cause and proposes a deterministic, local, report-only diagnostic plan without authorizing any new submit or broker action.

## Evidence (artifacts)

- Memo: `docs/ops/d3-749-supervised-micro-live-evidence-cycle.md`
- Submit session: `outputs/hyperliquid_submits/20260514_090121_hyperliquid_submit_8ae1921/`
  - `hyperliquid_submit_response.json`
  - `hyperliquid_signed_action.json`
  - `session_status.json`

### Extracted payload facts (from submit response)

- symbol: `ETH`
- resolved_asset: `1`
- size `s`: `0.00661492`
- reduce_only `r`: `false`
- error: `Order has invalid size.`

## What this rejection is (and is not)

Not:
- missing signing key
- missing account id
- min notional
- tick size

This rejection is consistent with:
- quantity precision / size step constraints per market (venue-side constraints)
- local formatting that emits a size string the venue rejects

## Working hypothesis

QuantLab currently formats Hyperliquid order size with a fixed decimal formatting rule:

- `_format_hyperliquid_size(quantity)` emits up to 8 decimals (then strips trailing zeros).

If Hyperliquid enforces per-asset size precision constraints (for example `szDecimals` or an implicit step size), then emitting 8-decimal sizes can violate the constraint for assets that allow fewer decimals.

### Code evidence

- Size formatting is currently asset-agnostic: [hyperliquid.py](file:///c:/dev/quantlab/src/quantlab/brokers/hyperliquid.py#L2112-L2114)
- Perp market lookup only maps `symbol -> resolved_asset` and does not surface size constraints into preflight artifacts: [fetch_hyperliquid_perp_market](file:///c:/dev/quantlab/src/quantlab/brokers/hyperliquid.py#L1971-L1990)

## Root cause candidate (classification)

classification:
- root_cause_candidate: `missing_local_size_constraints_quantization`
- signal: `remote_submit_rejected_invalid_size`
- policy: `no_retry`

## Deterministic diagnostic plan (report-only)

Goal:
- detect “likely invalid size” locally before submit by validating the formatted `s` against per-asset size constraints

Requirement:
- persist per-asset size constraints into an existing read-only artifact (preflight or signed-action report) so the check is deterministic and does not require a submit attempt

Proposed checks (deterministic once constraints are surfaced):
- Extract formatted `size_s` from `action_payload.orders[0].s`
- Extract `szDecimals` (and any min size) from venue metadata and persist it
- Validate:
  - `decimal_places(size_s) <= szDecimals`
  - `size` is a multiple of `10^-szDecimals`
- If violation:
  - add a readiness reason such as `size_precision_violation`
  - include a suggested “floor-to-step” size string and the implied effective notional

## Non-goals

- No retry of #749
- No second submit
- No Stage E opening
- No runtime changes in this issue
