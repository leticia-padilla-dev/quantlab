# Paper Trading MVP Acceptance Contract v0

Status: target acceptance contract, not an implemented runtime or permission to trade live. Baseline: Wave 1 certified on `main` at `5dcaf2e48773b73d0f7945d39d1a590b99b1ed73`. Wave 2 and live execution remain closed.

## Purpose and boundary

The product passes only when one fixed strategy can run automatically in paper, retain an unambiguous session and accounting history across defined faults, stop on uncertainty, and leave enough evidence to reconstruct every decision and simulated execution. This is an **operational product** test, not proof of strategy profitability, research promotion, broker readiness, or live authority. A simple `operational_test_strategy` may be used without becoming `promotion_eligible`; a `paper_strategy_trial` remains subject to [paper-modes-governance.md](paper-modes-governance.md) and [research-promotion-policy.md](research-promotion-policy.md).

QuantLab owns session/strategy identity, quantitative provenance and authority, evidence acceptance, independent accounting verification, lifecycle/promotion decisions, capital authority, and any future Strategy Health policy. An external engine may own market-event processing and simulated order/position mechanics, but never promotion or capital authorization. The existing `ExecutionIntent` / `ExecutionContext` terminology remains useful for intent and routing identity; this document does not change their implementation.

This contract is prospective. Existing `run --paper` artifacts and supervised-paper runbooks are evidence sources, not proof that unattended execution or same-session recovery already exists. No scenario below authorizes a broker submit. The [live freeze](ops/v0.1-hardening-live-freeze.md) remains in force.

## Test protocol and verdict

Before engine comparison, freeze one spike profile: strategy ID/version and config digest; one or two markets; one-position limit; deterministic feed with entry, hold, exit and no-trade cases; simulated fee/slippage and instrument precision policies; STOP-with-position disposition; and fault injection points. Use the **same** profile and criteria for every engine. The Adopt/Build spike uses deterministic fixtures, fault injection, native-capability inspection and short runtime smoke where needed; it does **not** require the full real-time paper observation window. Before final MVP certification, predeclare that bounded observation window without seeing its results.

Record for every scenario: `scenario_id`, tested code/engine version, setup and fault, expected state, actual state, canonical artifact paths, event trace, independent reconciliation result, and verdict. The spike classifies applicable scenarios as `PASS`, `PARTIAL` or `FAIL` for engine selection; these are not final MVP verdicts. Final MVP acceptance, after engine selection and build, requires every applicable `MUST` end-to-end, definitive evidence and the predeclared real-time paper observation (including M02). Identity/state and counts compare exactly. Monetary amounts use a declared decimal, currency/fee precision, rounding, and reconciliation policy; market price/quantity use declared tick/lot rules. No arbitrary float tolerance. Missing, contradictory, or non-reconstructible definitive evidence is `FAIL`, not an inferred success. `SHOULD` cannot compensate for a failed `MUST`.

The minimum paper evidence baseline remains `outputs/paper_sessions/<session_id>/` with `session_metadata.json`, `session_status.json`, `report.json`, and `trades.csv`, as defined by the [artifact completeness contract](ops/paper-artifact-completeness-contract.md). The MVP may require additional authoritative intent, event, state-snapshot, accounting, and reconciliation records; this document specifies their information, not new filenames or schemas. Logs and health summaries aid diagnosis but cannot replace canonical per-session truth. Quantitative artifacts entering ranking, forward selection, or promotion must retain the [provenance/authority contract](run-artifact-contract.md).

## MUST — MVP acceptance scenarios

Each scenario is evaluated as `capability → invariant → setup/scenario → fault/action → expected behavior → evidence → PASS/FAIL`.

### M01 — START with one fixed strategy

- **Capability:** create a paper session.
- **Invariant:** one stable `session_id` binds mode `paper`, strategy ID/version, frozen config, source provenance, market, execution account scope and engine version; no implicit promotion or live authority.
- **Setup/scenario:** empty session root, fixed strategy and one-position limit.
- **Fault/action:** issue START once, then repeat the same start request.
- **Expected behavior:** exactly one logical session; duplicate request returns the same session or a deterministic rejection, never a second active executor.
- **Evidence:** metadata, config digest, status transition and start-request identity.
- **PASS/FAIL:** PASS only if identity and active-executor count are exact and canonical evidence is complete; otherwise FAIL.

### M02 — Unattended paper cycle

- **Capability:** automatic decisions and simulated execution.
- **Invariant:** no operator step is needed between scheduled market events, strategy decisions, intents and paper outcomes; at most one position is open.
- **Setup/scenario:** frozen feed containing at least two decision cycles, one actionable signal and one no-trade; then the predeclared bounded real-time paper window.
- **Fault/action:** let both runs proceed without manual sequencing.
- **Expected behavior:** decisions and paper actions advance or stop by policy, with no silent stall or extra position.
- **Evidence:** timestamped feed/decision/intent/outcome trace, position snapshots and operator-action log.
- **PASS/FAIL:** PASS only if both fixture and bounded observation complete without intervention or unexplained gaps; otherwise FAIL.

### M03 — Restart with an open position

- **Capability:** recover an interrupted logical session.
- **Invariant:** the same `session_id`, position identity and accounting lineage survive; a new process/execution instance must not become a new trade or reuse stale authority.
- **Setup/scenario:** paper entry acknowledged and position open.
- **Fault/action:** terminate the process abruptly, then restart.
- **Expected behavior:** recovery reconciles persisted and engine state before new strategy actions; any mismatch stops. No duplicate entry or silently reset balance.
- **Evidence:** pre-crash and post-restart snapshots, instance IDs, position/trade IDs, reconciliation result and restart trace.
- **PASS/FAIL:** PASS only if identity and ledger continuity match exactly and no duplicate occurs; otherwise FAIL.

### M04 — Interrupted persistence

- **Capability:** durable state and artifact lifecycle.
- **Invariant:** a partial write cannot become an apparently successful canonical state.
- **Setup/scenario:** session has a previously valid state and a pending state/evidence update.
- **Fault/action:** interrupt the write at the defined fault point and restart.
- **Expected behavior:** recover the previous valid state or classify the update as incomplete/ambiguous and stop; never silently discard an acknowledged action or fabricate terminal success.
- **Evidence:** before/after artifact integrity, durable sequence or checkpoint, recovery classification and write-fault trace.
- **PASS/FAIL:** PASS only if an operator can distinguish committed from partial state and reconcile it; otherwise FAIL.

### M05 — Repeated intent after failure

- **Capability:** idempotent intent handling.
- **Invariant:** one logical `intent_id` causes at most one simulated execution, including after retry or restart.
- **Setup/scenario:** create an intent; interrupt between dispatch and acknowledgement.
- **Fault/action:** replay the same intent after recovery.
- **Expected behavior:** inspect durable/engine outcome first; return the existing result or stop for reconciliation. Never submit a second action while outcome is unknown.
- **Evidence:** intent ID, attempt IDs, engine order ID, acknowledgements, trade ledger and duplicate count.
- **PASS/FAIL:** PASS only if duplicate execution count is zero and the outcome is provable; otherwise FAIL.

### M06 — Ambiguous execution or state

- **Capability:** stop-on-ambiguity and reconciliation.
- **Invariant:** unknown acknowledgement, conflicting position, missing canonical artifact or stale state never permits another strategy action or blind retry.
- **Setup/scenario:** inject one contradictory or missing outcome.
- **Fault/action:** advance the decision clock and request retry/resume.
- **Expected behavior:** enter `reconciliation_required` or an equivalent explicit blocked posture; stop new actions until independent state resolves the ambiguity and an authorized resume decision is recorded.
- **Evidence:** conflicting inputs, stop timestamp, zero post-stop intents, reconciliation trace and final classification.
- **PASS/FAIL:** PASS only if it fails closed and no action crosses the ambiguity boundary; otherwise FAIL.

### M07 — Reconstructible accounting

- **Capability:** verify positions, trades and net paper P&L.
- **Invariant:** opening balance + cash flows − fees/costs and position marks reconcile to closing cash/equity under the frozen precision policy; zero-trade periods are explicit.
- **Setup/scenario:** deterministic entry, partial/full exit, fee, slippage and no-trade fixture.
- **Fault/action:** independently recompute from recorded events, including after restart.
- **Expected behavior:** position quantity, trade count, realized/unrealized P&L, fees and costs match the independent ledger; missing inputs stop acceptance.
- **Evidence:** trade/fee ledger, price source, precision policy, snapshots and signed reconciliation difference.
- **PASS/FAIL:** PASS only if identities/counts are exact and monetary/market values satisfy their declared policies; otherwise FAIL.

### M08 — START / PAUSE / STOP transitions

- **Capability:** operator control.
- **Invariant:** commands have explicit, durable and observable effects; repeated commands are idempotent.
- **Setup/scenario:** session running with a pending decision and no open position.
- **Fault/action:** PAUSE, repeat PAUSE, resume via START, then STOP and repeat STOP.
- **Expected behavior:** PAUSE blocks new strategy intents while read-only monitoring/reconciliation continues; START resumes only from reconciled state; STOP blocks further strategy intents and reaches an explicit disposition. No command silently changes strategy/config.
- **Evidence:** command IDs, state transitions, pending-intent handling and zero unintended actions.
- **PASS/FAIL:** PASS only if every transition and repeated command has the declared effect; otherwise FAIL.

### M09 — STOP with a position open

- **Capability:** safe operator stop under exposure in paper.
- **Invariant:** STOP never silently marks the session complete, loses the position, or implies liquidation.
- **Setup/scenario:** one open paper position and possibly one pending simulated order; freeze the planned hold/close disposition before the test.
- **Fault/action:** issue STOP and restart the process.
- **Expected behavior:** block new strategy entries; cancel/reconcile pending actions; preserve the open position and accounting until an explicitly evidenced hold/close disposition. If outcome is unclear, remain blocked and require operator action.
- **Evidence:** STOP acknowledgement, pending-order outcome, position snapshot, ledger and operator-visible next action.
- **PASS/FAIL:** PASS only if the position and required next action remain reconstructible after restart; otherwise FAIL.

### M10 — Causal evidence

- **Capability:** reconstruct what happened without operator memory.
- **Invariant:** each decision links when/why it occurred to input/config/source, intent or no-trade reason, attempted action and observed outcome; canonical state is not inferred from console logs.
- **Setup/scenario:** entry, no-trade, retry, PAUSE, STOP and one injected failure.
- **Fault/action:** reconstruct the timeline from persisted evidence alone.
- **Expected behavior:** a second reviewer reaches the same ordering, terminality, severity and next action; gaps or conflicting artifacts force stop.
- **Evidence:** ordered decision/intent/attempt/outcome records, provenance/integrity checks, canonical status/report/trades and reconciliation record.
- **PASS/FAIL:** PASS only if every causal link and operator conclusion is reproducible; otherwise FAIL.

### M11 — Paper has no real-money capability

- **Capability:** isolate paper execution from live mutation.
- **Invariant:** when live authority is false, QuantLab and any paper engine cannot submit, cancel or otherwise mutate orders on a real venue account.
- **Setup/scenario:** inspect paper process/container, credential scopes and available routes; use public market data or genuinely read-only credentials where needed.
- **Fault/action:** attempt every configured live-mutation path under paper mode.
- **Expected behavior:** no mutating credential is accessible to the paper runtime and no effective live submit, cancel or mutation route exists; a UI toggle or software flag alone is insufficient. Restart cannot restore capacity.
- **Evidence:** mandatory redacted credential-scope inventory, route/capability inventory and denied-attempt/restart trace; independent venue activity is additional evidence only if a dedicated venue account/subaccount is used later (M13).
- **PASS/FAIL:** PASS requires demonstrated absence of accessible mutating credentials and effective mutation routes, including after restart. If venue validation is used, QuantLab-attributable real orders and fills must also be exactly zero. Missing capability proof, an effective mutation path or unexplained venue activity is FAIL; a real account is not required for the primary proof.

### M12 — External-engine authority bypass (conditional MUST)

- **Capability:** contain an adopted engine behind QuantLab authority.
- **Invariant:** engine mechanics never grant independent capital or promotion authority.
- **Setup/scenario:** only when evaluating an external engine; paper credentials/routes remain non-mutating.
- **Fault/action:** try native UI, API, restart/resume, scheduler, strategy callback, retry path, manual engine command and stale pre-restart authorization.
- **Expected behavior:** every path is denied real mutation and cannot bypass QuantLab's authority boundary; ambiguity fails closed.
- **Evidence:** per-path result matrix, redacted capability/credential proof, QuantLab authority record, engine trace and venue records where applicable.
- **PASS/FAIL:** PASS only if every listed bypass path is tested and none can acquire real authority; any untested or successful path is FAIL.

### M13 — Dedicated execution account attribution (conditional MUST)

- **Capability:** independently validate venue truth when a venue is involved.
- **Invariant:** without live authority, no QuantLab route produces orders or fills in QuantLab's dedicated account/subaccount; unrelated manual activity cannot mask or mimic a result.
- **Setup/scenario:** before any future venue-connected validation, provision a dedicated account/subaccount with no shared manual activity and read-only means to inspect its records.
- **Fault/action:** run the boundary tests, including restart and attempted bypass.
- **Expected behavior:** venue orders/fills/cancels/positions agree with the internal authority and engine traces; any unexplained mutation is a hard failure, regardless of internal logs.
- **Evidence:** venue account activity first, QuantLab authority records second, engine logs third; account identity and time window are bound to the test.
- **PASS/FAIL:** PASS only if attribution is unambiguous and real mutation count without authority is zero; otherwise FAIL. This requirement does not authorize live testing now.

## SHOULD after the first MVP

- Longer predeclared paper observation across additional market conditions, with explicit degradation and quarantine signals.
- Richer operator views and Strategy Health, provided they remain derived from canonical state.
- More than one strategy or market only after one-strategy identity, accounting and stop semantics pass repeatedly.

## OUT OF SCOPE

Auto-modifying or automatically optimizing strategies; live trading or reopening the live freeze; capital scaling; champion/challenger; regime awareness; Quant Pulse; complete Strategy Health; simultaneous multiple strategies; general registry/framework work; and Wave 2 unless a specific failed acceptance scenario proves an indispensable dependency. Passing this contract does **not** promote a strategy or authorize capital.

## External-engine comparison and decision

The Adopt/Build spike evaluates Freqtrade first against each applicable M01–M13 scenario using the frozen profile, deterministic fixtures, fault injection, native-capability inspection, restart/idempotency/accounting/authority tests and short runtime smoke where needed. It selects an engine; it does not certify the Paper MVP or require the full real-time observation window. If Freqtrade fails a critical invariant or needs an unreasonable gap, evaluate NautilusTrader against **exactly the same** profile and thresholds. Do not reinterpret `PAUSE`, restart, accounting, or authority for a preferred engine. No engine is implemented or selected by this document.

| Verdict | Meaning |
|---|---|
| `PASS` | The applicable invariant is demonstrated under the spike harness, including any tested QuantLab-owned adapter boundary; this is not final MVP certification. |
| `PARTIAL` | A bounded gap and proposed owner/mitigation are identified, but the invariant has not yet been proven. Not an MVP pass. |
| `FAIL` | Invariant is violated, bypass exists, evidence is absent/contradictory, or the gap cannot be bounded. |

For each applicable scenario, record engine-native result, QuantLab-owned gap, proposed mitigation, spike evidence and `PASS` / `PARTIAL` / `FAIL`. A critical `PARTIAL` remains unproven; a critical `FAIL` or unreasonable/unresolved gap triggers the NautilusTrader comparison. If neither can meet the critical contract, define only the demonstrated missing component for a build decision. Then record an ADR, select the engine and make an **ENGINE FREEZE**: stable until failed acceptance or operational evidence invalidates it, not reopened for curiosity or tool preference. Only after that decision and MVP construction, run all applicable `MUST` scenarios end-to-end with definitive evidence and the predeclared real-time paper observation; only then may Paper MVP be declared `PASS`. Do not search indefinitely.

## Relationship to current documents

- [Paper restart/resume posture](ops/paper-restart-resume-posture.md) currently requires a **new** session ID after interruption and says resume is unsupported. M03 is a future MVP acceptance target, not a retroactive change to that supervised-paper rule; an implementation must explicitly reconcile the contracts before claiming PASS.
- [Paper modes governance](paper-modes-governance.md) and [research promotion policy](research-promotion-policy.md) require research evidence for a promotable `paper_strategy_trial`. This MVP may use an operational test strategy like infrastructure smoke, but its PASS cannot be treated as a strategy trial or promotion.
- [Paper terminality](ops/paper-session-terminality-contract.md), [artifact completeness](ops/paper-artifact-completeness-contract.md) and [canonical-vs-observability boundary](ops/paper-canonical-vs-observability-boundary.md) remain the current interpretation rules. New active/recovered/stopped-with-position states require an explicit compatible lifecycle contract; this document does not silently add them to today's schema.
- `.agents/current-state.md` is synchronized with Wave 1 completion, this contract as the next checkpoint, the subsequent Adopt/Build spike, closed live/capital authority and Wave 2 not started. The existing [roadmap](roadmap.md) retains older D.2/D.3 priorities as historical direction where applicable; this contract does not rewrite it or reopen live execution.
