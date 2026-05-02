# Supervised Broker Runbook

This runbook explains how to operate QuantLab's current supervised broker corridors as a bounded, artifact-first workflow.

It is intentionally short.

The goal is not to describe every CLI flag.
The goal is to make the current happy path and failure path repeatable for a human operator.

## 1. Operating Rule

QuantLab's current broker work should be treated as:

- supervised
- artifact-first
- conservative
- evidence-producing

It should not be treated as:

- autonomous live trading
- retry-happy execution
- a UI-driven workflow

The key discipline is:

1. build or inspect the local artifact
2. confirm the gate
3. submit once
4. reconcile before acting again

If state becomes ambiguous, stop widening actions and inspect the artifacts already written.

## 2. Promotion Floor Before Broker Work

Before using a broker-facing corridor, the candidate should already have:

- a paper-backed result worth promoting
- a clearly chosen symbol, side, quantity, and notional
- a deliberately small first size
- an operator willing to review the resulting artifacts

Practical rule:

- paper is still the promotion floor
- broker work begins only after the operator is comfortable that the paper result is worth a tightly supervised real-world check

## 2.5. Readiness Check Before The First Evidence Pass

Before attempting the first supervised broker evidence run, generate a readiness artifact:

```bash
python main.py --broker-evidence-readiness-outdir outputs/broker_evidence
```

Hyperliquid is the preferred first corridor for the current execution direction.

If you already know which corridor you want to exercise first, make it explicit:

```bash
python main.py --broker-evidence-readiness-outdir outputs/broker_evidence --broker-evidence-corridor hyperliquid
python main.py --broker-evidence-readiness-outdir outputs/broker_evidence --broker-evidence-corridor kraken
```

Use this check to fail early on:

- missing broker credentials
- missing Hyperliquid execution identity inputs
- missing runbook/documentation continuity

The command writes `broker_evidence_readiness.json` even when the corridor is not ready yet.

## 3. Happy Path: Kraken Supervised Corridor

This is the current narrow Kraken path under `outputs/broker_order_validations/`.

### Step 1: create a validation session

```bash
python main.py --kraken-order-validate-session --broker-symbol ETH-USD --broker-side buy --broker-quantity 0.25 --broker-notional 500 --broker-account-id acct_demo
```

This writes a canonical validation session under:

```text
outputs/broker_order_validations/<session_id>/
```

### Step 2: inspect the validation result

```bash
python main.py --broker-order-validations-show outputs/broker_order_validations/<session_id>
```

### Step 3: approve the session locally

```bash
python main.py --broker-order-validations-approve outputs/broker_order_validations/<session_id> --broker-approval-reviewer marce --broker-approval-note "Approved after validate-only review"
```

### Step 4: materialize the pre-submit bundle

```bash
python main.py --broker-order-validations-bundle outputs/broker_order_validations/<session_id>
```

### Step 5: materialize the supervised submit gate

```bash
python main.py --broker-order-validations-submit-gate outputs/broker_order_validations/<session_id> --broker-submit-reviewer marce --broker-submit-confirm --broker-submit-note "Ready for supervised submit review"
```

### Step 6: perform the first real supervised submit

```bash
python main.py --broker-order-validations-submit-real outputs/broker_order_validations/<session_id> --broker-submit-reviewer marce --broker-submit-confirm --broker-submit-live --broker-submit-note "First supervised live submit"
```

### Step 7: reconcile if needed

```bash
python main.py --broker-order-validations-reconcile outputs/broker_order_validations/<session_id>
```

### Step 8: refresh normalized post-submit status

```bash
python main.py --broker-order-validations-status outputs/broker_order_validations/<session_id>
```

### Step 9: inspect operator pulse over the full root

```bash
python main.py --broker-order-validations-health outputs/broker_order_validations
python main.py --broker-order-validations-alerts outputs/broker_order_validations
```

## 4. Failure Path: Kraken

Stop the corridor at the first failing gate.

### Validation rejected

Meaning:

- the exchange-side validate-only path did not accept the order shape

What to do:

- inspect `broker_order_validate.json`
- adjust size, symbol, side, or account assumptions
- do not approve the session just to continue the flow

### Local approval not granted

Meaning:

- the session is not yet fit for submission

What to do:

- stop
- record the reason in the approval note or session review context
- do not bundle or gate a session that should not pass human review

### Submit becomes ambiguous

Meaning:

- a real submit was attempted but the effective remote state is still unclear

What to do:

1. inspect `broker_submit_response.json`
2. run `--broker-order-validations-reconcile`
3. run `--broker-order-validations-status`
4. inspect `broker_order_status.json`
5. inspect `--broker-order-validations-health` and `--broker-order-validations-alerts`

Do not:

- blindly re-submit
- create a second session just to “try again”
- assume absence of a clean local success message means the exchange never saw the order

## 5. Happy Path: Hyperliquid Supervised Corridor

This is the current narrow Hyperliquid path under `outputs/hyperliquid_submits/`.

### Step 1: preflight and readiness

```bash
python main.py --hyperliquid-preflight-outdir outputs/broker_preflight/hyperliquid_demo --broker-symbol ETH --execution-transport-preference websocket
python main.py --hyperliquid-account-readiness-outdir outputs/broker_preflight/hyperliquid_account_demo --execution-account-id 0x0000000000000000000000000000000000000000
```

### Step 2: build and sign the action locally

```bash
python main.py --hyperliquid-signed-action-outdir outputs/broker_preflight/hyperliquid_signed_action_demo --broker-symbol ETH --broker-side buy --broker-quantity 0.25 --broker-notional 500 --execution-account-id 0x0000000000000000000000000000000000000000 --execution-signer-id 0xSIGNER_ADDRESS --hyperliquid-private-key-env HYPERLIQUID_PRIVATE_KEY
```

### Step 3: create a canonical supervised submit session

```bash
python main.py --hyperliquid-submit-session outputs/broker_preflight/hyperliquid_signed_action_demo/hyperliquid_signed_action.json --hyperliquid-submit-reviewer marce --hyperliquid-submit-confirm --hyperliquid-submit-sessions-root outputs/hyperliquid_submits
```

### Step 4: refresh post-submit visibility

```bash
python main.py --hyperliquid-submit-sessions-status outputs/hyperliquid_submits/<session_id>
python main.py --hyperliquid-submit-sessions-reconcile outputs/hyperliquid_submits/<session_id>
python main.py --hyperliquid-submit-sessions-fills outputs/hyperliquid_submits/<session_id>
python main.py --hyperliquid-submit-sessions-supervise outputs/hyperliquid_submits/<session_id>
```

### Step 5: inspect operator pulse over the full root

```bash
python main.py --hyperliquid-submit-sessions-health outputs/hyperliquid_submits
python main.py --hyperliquid-submit-sessions-alerts outputs/hyperliquid_submits
```

### Step 6: use cancel only as an explicit supervised action

```bash
python main.py --hyperliquid-submit-sessions-cancel outputs/hyperliquid_submits/<session_id> --hyperliquid-cancel-reviewer marce --hyperliquid-cancel-confirm
```

### Step 6.5: generate a reduce-only close signed-action if a perp position remains open

After a filled perp entry, if Hyperliquid UI confirms a remaining open position, generate a supervised close signed-action before submitting. Do not close manually from the UI unless it is an emergency.

The close side is opposite to the entry side. The `--broker-reduce-only` flag sets `action_payload.orders[0].r = true`. Verify this in the artifact before approving submit.

```bash
python main.py \
  --hyperliquid-signed-action-outdir outputs/d3_446/close_q0005 \
  --broker-symbol ETH \
  --broker-side sell \
  --broker-notional 12 \
  --broker-quantity 0.005 \
  --broker-reduce-only \
  --broker-account-id $HYPERLIQUID_ACCOUNT \
  --broker-max-notional 20 \
  --broker-allowed-symbols ETH \
  --execution-account-id $HYPERLIQUID_ACCOUNT \
  --execution-signer-id $HYPERLIQUID_SIGNER_ID \
  --execution-signer-type direct \
  --execution-transport-preference websocket \
  --hyperliquid-private-key-env HYPERLIQUID_PRIVATE_KEY
```

Inspect the artifact before submitting:

```yaml
expected:
  action_payload.orders[0].b: false      # sell
  action_payload.orders[0].r: true       # reduce_only
  readiness_allowed: true
  value_readiness.value_sufficient: true
  identity_readiness.identity_ready: true
  signing_readiness.signing_ready: true
```

Submit the close through the canonical supervised session path (Step 3–5) only after explicit operator approval.

## 6. Failure Path: Hyperliquid

### Readiness or signer mismatch

Meaning:

- the account/signer arrangement is not yet trustworthy for submission

What to do:

- inspect `hyperliquid_account_readiness.json`
- inspect `hyperliquid_signed_action.json`
- stop if `readiness_allowed` is false or if `signature_state` is not `signed`

Do not submit an unsigned or mismatched artifact.

### Post-submit state remains unclear

Meaning:

- the session exists, but the effective lifecycle is still not obvious from a single artifact

What to do:

1. inspect `hyperliquid_submit_response.json`
2. run `--hyperliquid-submit-sessions-status`
3. run `--hyperliquid-submit-sessions-reconcile`
4. run `--hyperliquid-submit-sessions-fills`
5. run `--hyperliquid-submit-sessions-supervise`
6. inspect `--hyperliquid-submit-sessions-health` and `--hyperliquid-submit-sessions-alerts`

Do not:

- generate a second signed action just to “see if it lands”
- treat lack of immediate fill evidence as proof the order is gone
- use cancel until you have inspected the latest session state

## 7. Artifacts Worth Preserving

For a supervised broker run worth keeping, the minimum evidence pack is:

- source paper session id or rationale for promotion
- the first validation or signed-action artifact
- the approval or reviewer identity
- the first submit response artifact
- the latest reconciliation or status artifact
- the latest health and alerts snapshot for the root

This is the minimum useful pack for post-mortem review.

## 8. Minimal Operator Loop

When operating one supervised corridor:

1. choose the smallest realistic candidate worth promoting
2. create the first local broker artifact
3. inspect before approving or submitting
4. submit once
5. reconcile and refresh status before taking any second action
6. read root-level health and alerts
7. keep the artifact pack if the run is worth learning from

## 9. Boundary Notes

- these corridors are still supervised, not autonomous
- the current priority is not adding more surface area, but producing evidence and hardening the exact failure point that appears in real use
- paper, broker, and Hyperliquid surfaces should be treated as one promotion ladder, not as unrelated demos

## 10. Related Documents

- [README.md](../README.md)
- [cli.md](./cli.md)
- [paper-session-runbook.md](./paper-session-runbook.md)
- [broker-safety-boundary.md](./broker-safety-boundary.md)
- [roadmap.md](./roadmap.md)

## 11. D.3 Micro-Live Gate — Hyperliquid Completion Record (#446)

### Outcome

Issue #446 completed a full QuantLab-mediated Hyperliquid micro-live cycle: supervised entry, supervised reduce-only close, no open position remaining.

#### Entry session

Path: `outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49`

- side: buy
- symbol: ETH perp
- filled_size: 0.005 ETH
- order_state: filled
- reconciliation_state: filled
- close_state: closed
- fill_count: 1
- alert_status: ok
- no retry performed

#### Reduce-only close session

Path: `outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8`

- side: sell
- reduce_only: true
- symbol: ETH perp
- filled_size: 0.005 ETH
- order_state: filled
- reconciliation_state: filled
- close_state: closed
- fill_count: 1
- alert_status: ok
- no retry performed

#### Final verification

Hyperliquid UI confirmed no open ETH perp position after the reduce-only close. No manual close was performed. No extra submit was performed outside the approved flow.

### Blockers discovered and resolved

Each rejection produced a targeted fix before the next attempt. No retry was performed within the same session.

| PR | Fix |
|----|-----|
| #494 | Tick-size quantization: price must be divisible by venue tick (5 sig-fig rule, ETH perp → 1 decimal place) |
| #495 | IOC price buffer: buy = mid + 5 bps, sell = mid − 5 bps, to ensure order is executable |
| #496 | Top-of-book IOC pricing: use best_ask/best_bid from L2 book instead of mid_price |
| #497 | Identity and signing readiness gate: derived_signer must match declared_signer before action is signed |
| #498 | Minimum order value gate: effective notional (price × quantity) must be ≥ $10 USD |
| #499 | Reduce-only close support: `--broker-reduce-only` flag sets `action_payload.orders[0].r = true` |

### Health note

Global submit health may show `critical` even after a successful cycle because QuantLab preserves historical rejected sessions as evidence. This is correct behavior. Assess the latest session state, not the root aggregate, when evaluating whether a cycle succeeded.

## 12. Gate Rules for Future Hyperliquid Submits

Before submitting any Hyperliquid order, the signed-action artifact must satisfy all of the following:

- `readiness_allowed: true`
- `signature_envelope.signature_state: signed`
- `identity_readiness.identity_ready: true`
- `signing_readiness.signing_ready: true`
- `value_readiness.value_sufficient: true` (effective notional ≥ $10 USD)
- top-of-book present in public_preflight (`best_ask` / `best_bid` not null), or the fallback to mid_price is explicitly reviewed and accepted
- price is tick-quantized (5 significant figures, buy rounds up, sell rounds down)
- IOC buffer applied (5 bps from executable side)
- explicit operator approval given before submit call

Additional rules for close flows:

- `action_payload.orders[0].r: true` for any reduce-only close
- close side must be opposite to the open position side
- close quantity must not exceed the open position size
- artifact reviewed before submit; no auto-close from UI unless emergency

Rejection handling:

- do not retry within the same session after an exchange rejection
- generate a new signed-action artifact, inspect it, and obtain approval before a second attempt
- record each rejection as a named session; do not overwrite prior artifacts
