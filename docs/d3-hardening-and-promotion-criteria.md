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

## 4.6 Current Checklist Validation Status

This section classifies each hardening criterion (4.1–4.5) against the evidence produced by #446 and the gate rules documented in `docs/supervised-broker-runbook.md` § 11–12. The goal is to separate evidence that has been proven from gaps that require operator review and declaration. Stage E remains explicitly blocked pending operator declarations on all pending items.

### 4.6.1 Runbook Completeness

**Classification: `pending_operator_review`**

**Evidence Satisfied:**
- The supervised entry flow (runbook § 5) was executed end-to-end in #446 entry session: `outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49`
  - Entry: 0.005 ETH buy, filled on first attempt, no retry
  - Result: `filled` state with no ambiguity
- The reduce-only close flow (runbook § 6.5) was executed in #446 close session: `outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8`
  - Close: 0.005 ETH sell with `reduce_only: true` flag set
  - Result: `filled` state, position confirmed closed in Hyperliquid UI, no manual intervention

**Remaining Gap:**
- The completion of #446 proves the flow is *possible*, but does not prove that the operator can reconstruct it using *only* the runbook without consulting session history or prior execution context.
- Operator must confirm: "I can reconstruct the entry and close flows using only the runbook as a guide, without referencing the #446 session artifacts."

**Stage E Impact:** ⚠ Blocked. Cannot proceed until operator confirms runbook is sufficient for next iteration.

### 4.6.2 Alert Confidence

**Classification: `pending_operator_review`**

**Evidence Satisfied:**
- The runbook § 11 explains the distinction: global submit health aggregates historical rejected sessions as evidence of learning, not as proof of failure
- The #446 entry and close sessions both show `alert_status: ok` at the session level
- The health distinction between root-level aggregate and session-level state is fully documented

**Remaining Gap:**
- Operator must explicitly confirm understanding:
  1. They have read the alert distinction (global vs session-level) in runbook § 11
  2. They understand that `critical` at root level is expected and correct after multiple rejection sessions as historical evidence
  3. They know to assess the *latest session state*, not the root aggregate, when evaluating cycle success

**Stage E Impact:** ⚠ Blocked. Cannot proceed until operator declares understanding.

### 4.6.3 Reconciliation Confidence

**Classification: `pending_operator_review`**

**Evidence Satisfied:**
- The #446 entry session artifact is preserved at `outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49` with full reconciliation history
- The artifact shows the expected reconciliation path: `submitted_remote` → `filled` (no intermediate `reconciliation_required` because order ID was present)
- The runbook § 12 documents the stop condition explicitly: if `reconciliation_state` remains unclear, do not open a second session
- State transitions were deterministic; no manual interpretation was required

**Remaining Gap:**
- The criterion requires the operator to "describe what each `reconciliation_state` transition means"
- Operator must confirm: "I understand the reconciliation state machine transitions and can explain the difference between `submitted_remote`, `reconciliation_required`, and `filled` states, with specific reference to the #446 artifact."

**Stage E Impact:** ⚠ Blocked. Cannot proceed until operator confirms understanding of reconciliation state transitions.

### 4.6.4 Operator Stop-Control Confidence

**Classification: `pending_operator_review`**

**Evidence Satisfied:**
- The reduce-only close was executed successfully in #446: `outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8`
- The close side (sell) was opposite to the entry side (buy)
- No manual Hyperliquid UI close was performed; the supervised close artifact was used instead
- No extra submit was performed

**Remaining Gap:**
- The criterion requires the operator to confirm:
  1. They have reviewed the cancel flow (§ 6) and understand when it is and is not appropriate
  2. They understand that reduce-only close is the correct mechanism for a filled perp position, not Hyperliquid UI close
  3. They know that emergency UI close is the fallback of last resort only when QuantLab artifacts are unavailable or ambiguous

**Stage E Impact:** ⚠ Blocked. Cannot proceed until operator confirms cancel vs reduce-only rules and emergency fallback.

### 4.6.5 Evidence Trail Durability

**Classification: `pending_operator_review`**

**Evidence Satisfied:**
- Both #446 session paths are recorded in runbook § 11 with exact directory names:
  - Entry: `outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49`
  - Close: `outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8`
- Both directories contain full artifact packs (metadata, status, reconciliation, health)

**Remaining Gap:**
- The criterion requires confirmation that "the session directories exist locally and have not been modified after the cycle completed"
- Operator/local check must confirm: directories still exist on disk, are readable, and have not been modified or deleted since completion

**Stage E Impact:** ⚠ Blocked. Cannot proceed until operator confirms local session directories are intact and unmodified.

### 4.6.6 Stage E Gate Status

**Summary:**

| Criterion | Status | Operator Declaration Required |
|-----------|--------|------------------------------|
| Runbook Completeness | pending_operator_review | Can I reconstruct using only the runbook? |
| Alert Confidence | pending_operator_review | Do I understand the alert aggregation model? |
| Reconciliation Confidence | pending_operator_review | Can I explain each reconciliation state transition? |
| Operator Stop-Control | pending_operator_review | Do I understand cancel vs reduce-only rules? |
| Evidence Trail Durability | pending_operator_review | Are session directories intact and unmodified? |

**Decision:**

Stage E is explicitly blocked until the operator provides written confirmation on all five items above. Each confirmation should reference the specific section and artifact involved. When all five are confirmed, a new Stage E issue will be created with explicit scope, not implied from closure of this audit issue.

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
