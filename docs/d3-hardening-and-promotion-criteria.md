# D.3 Hardening and Stage E Promotion Criteria

**Date:** 2026-05-05
**Status:** post-D.3 initial validation — Stage E explicitly blocked

## 1. What D.3 Completed

Issue #446 completed a full QuantLab-mediated Hyperliquid micro-live cycle. The parent gate #413 is closed as completed.

Completed dependencies:

- #444 — broker dry readiness evidence
- #445 — allowlist + signed-action gate
- #446 — supervised micro-live session (entry filled, reduce-only close filled, no open position remaining)

The full evidence trail and gate rules from #446 live in:

- `docs/supervised-broker-runbook.md` § 11 (completion record with exact session paths)
- `docs/supervised-broker-runbook.md` § 12 (gate rules for future submits)

## 2. What D.3 Did Not Establish

D.3 initial validation does not mean:

- the flow is repeatable without operator friction
- Stage E is ready to open
- the current alert and health surfaces are calibrated for ongoing use
- reconciliation behavior is fully understood across ambiguous states
- operator stop-control has been exercised under pressure

These gaps are expected at initial validation. They define the hardening work.

## 3. Repeatability Expectations

A second D.3 cycle is considered repeatable when:

- the operator can reconstruct the full signed-action → submit → fill → close flow using only
  `docs/supervised-broker-runbook.md` and the gate rules in § 12, without consulting session history
- the signed-action artifact satisfies all gate rules in § 12 before any reviewer approval is requested
- no ad hoc adjustment is required at the point of signing (price, quantity, identity, or notional are
  correct on first generation)
- the post-submit reconciliation artifact reaches a terminal state (`filled` or `cancelled`)
  without manual interpretation of ambiguous JSON fields
- the root-level health and alert surface reflects the cycle outcome correctly within one supervision cycle

A cycle that requires operator interpretation beyond the runbook is not yet repeatable.

## 4. Promotion-Hardening Criteria Before Stage E

Stage E is explicitly blocked until all of the following are confirmed:

### 4.1 Runbook completeness

- [ ] The supervised-broker-runbook.md § 5 and § 6 paths have been exercised at least once
  using only the runbook as a guide (no session-history reference needed)
- [ ] The close flow (§ 6.5) is documented and was followed for the reduce-only close in #446

### 4.2 Alert confidence

- [ ] The operator understands why a root `alert_status: critical` can coexist with a successful
  most-recent session (historical rejected sessions are preserved as evidence)
- [ ] The operator can distinguish between a session-level alert and a root-level aggregate alert
  without inspecting raw JSON

### 4.3 Reconciliation confidence

- [ ] The operator has reviewed the reconciliation artifact for the #446 entry session and can
  describe what each `reconciliation_state` transition means
- [ ] The expected reconciliation path for a filled IOC order is documented:
  `submitted_remote` → `reconciliation_required` (if oid missing) or `filled`
- [ ] The operator knows the stop condition: if `reconciliation_state` remains unclear after
  running `--hyperliquid-submit-sessions-reconcile`, do not open a second session

### 4.4 Operator stop-control confidence

- [ ] The operator has reviewed the cancel flow (§ 6) and knows when it is and is not appropriate
- [ ] The operator has confirmed that a reduce-only close is the correct stop-control mechanism
  for a filled perp position, not the Hyperliquid UI cancel
- [ ] Emergency UI close is documented as the fallback of last resort when QuantLab artifacts are
  unavailable or ambiguous

### 4.5 Evidence trail durability

- [ ] Session paths for #446 are recorded with exact directory names in
  `docs/supervised-broker-runbook.md` § 11 (already done)
- [ ] The session directories exist locally and have not been modified after the cycle completed

## 5. Stage E Gate

Stage E opens only when:

1. All promotion-hardening criteria in § 4 are checked
2. The operator explicitly declares: "D.3 hardening complete — Stage E gate open"
3. A new issue is created for Stage E scope — it is never implied by closing this issue

Stage E is not a higher-frequency version of D.3. It is a qualitatively different stage and requires
a new scoping decision by the operator.

## 6. Related Documents

- [supervised-broker-runbook.md](./supervised-broker-runbook.md) — operational runbook with D.3 completion record (§ 11) and gate rules (§ 12)
- [roadmap.md](./roadmap.md) — stage definitions and promotion ladder
- [hyperliquid-boundary-review.md](./hyperliquid-boundary-review.md) — venue contract gap analysis
- [execution-context-layer.md](./execution-context-layer.md) — signer/routing identity model
