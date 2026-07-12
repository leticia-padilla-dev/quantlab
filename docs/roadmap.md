# QuantLab Roadmap

This roadmap defines the strategic direction and stage semantics for QuantLab. It is not a sprint plan.

> **Operational source of truth**: For the current executable priority, use `.agents/current-state.md`. This roadmap defines where the system is heading; `current-state.md` defines what the next concrete step is.

QuantLab is evolving toward a broker-connected supervised execution system, with controlled automation only after safety, evidence, observability, and operator-control gates are proven. It is not moving into broad automation now. The current frontier is operational hardening: Desktop/Operator Workspace stabilization, Legacy retirement, D.2/D.3 evidence hardening, and controlled promotion discipline.

Product framing:

- QuantLab is a local-first quantitative research and supervised execution system
- it may support modern execution venues, including web3-native venues, without becoming a crypto or AI marketing shell
- the roadmap prioritizes execution safety, signer correctness, evidence quality, and operator control before broader venue or automation power
- QuantLab should not be reframed as a crypto app, an AI trading platform, an automation-first system, or a generic broker dashboard

Strategic evolution order:

1. research reliability
2. paper-trading discipline
3. execution safety
4. broker boundary hardening
5. supervised live execution
6. controlled automation

Performance rule:

- stay Python-first by default
- treat native acceleration as a measured hotspot tactic, not as a product-wide rewrite plan
- prefer narrow compute kernels over multi-module language migration

The key rule remains the same:

- do not move into live execution before the paper, safety, and observability layers are mature

Minimum promotion policy:

- do not promote a stage if live or broker-facing work still depends on ad hoc local secret handling
- do not promote a stage if canonical critical alert coverage is missing for the failures that stage is supposed to survive
- treat missing alert artifacts or unclear secret boundaries as promotion blockers, not polish debt

## Current Position

QuantLab has already completed most of the original research foundation and quantitative robustness work.

### Effectively completed

- project packaging and modular source layout
- data ingestion and local artifact persistence
- indicators and feature preparation
- strategy abstraction and research execution flows
- backtesting and baseline metrics
- walk-forward / forward-evaluation flows
- canonical run artifacts and run history indexing
- stable machine-facing CLI and contract surfaces for integration
- a first repository-level decision on native acceleration strategy, with the backtest engine identified as the first realistic hotspot candidate if profiling justifies it

### In progress / partially completed

- paper-trading operationalization
- supervised broker submit safety, reconciliation, and post-submit visibility
- initial real-execution safety and Kraken boundary work
- initial supervised Hyperliquid signed-submit work behind the shared execution boundary
- external-consumer contract stability at the local CLI/artifact boundary
- Desktop/UI operator workspace architecture and shell hardening

### Not started as production capability

- broad multi-venue live routing beyond the first implemented boundary
- automated live trading
- learned-model production promotion

## Stage A - Foundations

Status: completed

Scope:

- `pyproject.toml` packaging
- modular `src/` layout
- core data ingestion
- indicator layer
- strategy interface
- backtest engine
- minimal metrics

Exit condition:

- the system runs end-to-end and strategies can be compared reproducibly

## Stage B - Quantitative Robustness

Status: completed

Scope:

- slippage and fee handling
- report generation
- walk-forward style evaluation
- stronger artifact traceability
- run comparison and indexing

Exit condition:

- research outputs are strong enough to reject weak strategies and compare plausible ones without obvious bias or operational ambiguity

## Stage C - Paper Trading Foundation

Status: mostly completed

Scope already present in the repo:

- paper-oriented execution path
- trade logging
- forward-session artifacts
- portfolio aggregation over forward sessions

Remaining gap:

- this still needs to behave like an operational paper-trading system, not only a research extension

Exit condition:

- QuantLab can simulate live behavior without capital at risk and preserve a complete audit trail for each paper session

## External Consumer Contract Stability

Status: completed as a former Stepbit-specific active track; reusable contract semantics remain maintained

This was historically developed as a Stepbit-facing readiness track. Stepbit is
now retired from the active QuantLab architecture, roadmap, and future delivery
planning.

The remaining valid scope is generic external-consumer contract stability.
QuantLab does not maintain an active Stepbit integration stage.

Scope:

- stable `--json-request`
- stable `--signal-file`
- stable `report.json.machine_contract`
- canonical run artifacts
- deterministic `--check` and `--version`
- automatic refresh of `runs_index.*`

External-consumer boundary rule:

External consumers may invoke QuantLab only through stable producer-side
contracts. No external orchestration layer may compensate for missing QuantLab
contracts with private logic. This means:

- no mocks to hide missing QuantLab contracts
- no consumer-side workaround for missing evidence artifacts
- no external orchestration absorbing QuantLab authority

Exit condition:

- external orchestration can invoke QuantLab as a reliable local execution engine without guessing at output structure

## Stage P.0 - Auxiliary Pre-Trade Risk Workbench

Status: proposed auxiliary subsystem track

Goal:

- add a bounded pre-trade planning layer to QuantLab without folding it into the
  backtest engine or venue execution adapters

Scope:

- new `src/quantlab/pretrade/` package
- deterministic trade-plan artifacts under `outputs/pretrade_sessions/`
- optional conversion into draft `ExecutionIntent`
- policy-aware pre-trade validation before adapter interaction
- bounded artifact-driven visualization in `research_ui`

Architectural rule:

- the workbench remains auxiliary
- QuantLab CLI and safety boundary remain sovereign
- the UI may visualize and compare plans, but must not own execution policy

See also:

- [docs/pretrade-risk-workbench-roadmap.md](./pretrade-risk-workbench-roadmap.md)
- [docs/pretrade-calculator-boundary.md](./pretrade-calculator-boundary.md)

Exit condition:

- QuantLab can generate and inspect deterministic pre-trade plans that improve
  operator discipline before paper or broker-facing actions without changing
  core engine responsibilities

## Transversal Capability Track - Desktop / Operator Workspace

Status: in progress — active promotion-support path

Goal:

- provide a stable operator workspace for reviewing research, paper, and broker evidence without moving authority out of the engine

Scope:

- desktop shell architecture and typed desktop contracts
- operator-facing workstation surfaces for runs, compare, artifacts, paper ops, and system continuity
- workspace hierarchy, focus, and promotion visibility across native desktop surfaces
- browser-backed continuity only where the desktop still depends on transitional `research_ui` behavior

Architectural rule:

- Desktop is an operator workspace and review surface. It must not become a second product authority or execution authority.
- Desktop/UI is a transversal capability track, not a primary linear stage
- the engine, contracts, and canonical artifacts remain the authority
- the workspace should reduce operator ambiguity, not introduce a second product authority
- the accepted desktop target architecture now lives in [docs/desktop-target-architecture.md](./desktop-target-architecture.md)
- `research_ui` should be treated as transitional continuity, not as the permanent shell target

Current importance:

Desktop is part of the active promotion-support path because it reduces ambiguity around evidence review, launch continuity, artifact inspection, paper ops, broker supervision, and Legacy fallback removal. Progress on Desktop directly enables the D.2/D.3 hardening frontier by providing the operator workspace needed to review evidence artifacts reliably.

Legacy retirement note:

Legacy retirement is not cosmetic cleanup. It supports operator confidence by removing fallback-dependent data paths after React-native parity is proven. The Legacy shell should be treated as a deprecated fallback and behavioral reference only, not as architectural truth. No new data paths should depend on Legacy state after native parity is established.

Exit condition:

- QuantLab can expose research, paper, and execution evidence through a stable operator workspace with clear ownership, continuity, and promotion visibility

## Next Remaining Stages

## Stage C.1 - Paper Trading Operationalization

Status: supporting stage, no longer the primary bottleneck

Goal:

- turn the existing paper-trading capabilities into an operationally disciplined layer

Scope:

- stable paper session lifecycle and session naming rules
- operator-facing paper runbook
- clear signal/export surface for paper actions
- alerting hooks for paper sessions
- stronger distinction between research backtests and paper sessions
- explicit session health / failure reasons for paper mode

Exit condition:

- QuantLab can run paper sessions repeatedly with traceability, alerts, and enough operator confidence to treat them as a real dry operational environment

Minimum promotion signals:

- paper sessions produce canonical session artifacts with explicit terminal status
- the operator can distinguish research outputs from paper sessions without ambiguity
- paper-critical failures emit canonical alert artifacts instead of requiring log archaeology

Current interpretation:

- `Stage C.1` still matters because paper-session discipline remains the promotion floor for broker-facing work
- but it is no longer the main unresolved runtime frontier
- from the current repository state, paper work should now be prioritized when it strengthens operator visibility, promotion discipline, or broker-readiness handoff rather than treated as the dominant roadmap stage

## External Consumer Contract Hardening

Status: secondary follow-up, driven by consumer feedback

Goal:

- reduce friction for maintained external consumers once they begin consuming the QuantLab contract in earnest

Scope:

- deterministic integration fixtures for `run` and `sweep`
- stronger contract tests for machine-facing outputs
- runbook improvements for consumer-side validation
- any small producer-side contract hardening needed after real adapter feedback

Exit condition:

- consumer systems can validate QuantLab integration deterministically and repeatedly without live-market dependence

## Quant Pulse Signal Intake

Status: proposed auxiliary signal boundary

Goal:

- consume upstream Quant Pulse research intents without making QuantLab dependent on an external editorial authority

Scope:

- structured signal intake for `signal_summary`, `priority`, `affected_universe`, `bias`, `horizon`, `hypothesis_type`, `validation_goal`, and `invalidation_condition`
- routing signals into research workflows only when they improve validation, risk filters, or product priorities
- keeping QuantLab autonomous while allowing Quant Pulse to act as a signal filter and prioritization layer

Exit condition:

- QuantLab can ingest upstream signals as structured research prompts while still deciding independently what is worth testing, filtering, or ignoring

## Stage D.0 - Real Execution Safety Boundary

Status: initial boundary slice implemented

Goal:

- define the safety layer before allowing real broker-connected order flow

Scope:

- `BrokerAdapter` as the broker-agnostic execution boundary
- execution-policy model
- max position size rules
- daily / session loss limits
- max concurrent exposure rules
- circuit-breaker and kill-switch behavior
- explicit failure-state handling
- broker credential boundaries and secret handling
- dry-run execution audit format

Initial slice already present:

- `ExecutionIntent`
- `ExecutionContext`
- `ExecutionPolicy`
- `ExecutionPreflight`
- `BrokerAdapter` contract
- deterministic local rejection before any exchange-specific adapter work

Exit condition:

- the system has a credible safety envelope and a broker abstraction that can reject unsafe execution decisions before a broker is connected

## Broker Integration Strategy

The first real execution-venue integration should follow this decision framework:

- define and stabilize `BrokerAdapter` before integrating any exchange-specific backend
- keep `Hyperliquid` as the active execution-venue target for personal connection and supervised practical use
- keep `Kraken` as implemented compatibility/history rather than the active next target
- consider `Bitget` as optional later comparison work after `Hyperliquid`, not the default next venue
- treat `Binance` as optional later comparison work, not the default next venue
- treat CCXT as optional acceleration for prototypes, smoke tests, or broad exchange experimentation, not as the authority of the execution design

Rationale:

- Hyperliquid is the preferred active venue because it tests whether the current abstraction can handle a high-performance onchain order-book venue, not only a conventional CEX-style broker
- Kraken remains useful as compatibility history and a reference implementation, but it is no longer the active next strategic target
- Binance remains useful later as an additional comparison backend, but it is no longer the default next strategic target
- CCXT is useful when speed matters, but native integrations remain preferable when QuantLab needs tighter control over errors, rate limits, retries, and private execution flows

Architectural rule:

- strategies, risk policy, and execution safety must depend on `BrokerAdapter`, never on exchange-specific code
- `BrokerAdapter` remains the current code name, but it should now be interpreted as an execution-venue boundary rather than only a traditional broker boundary

## Stage D.1 - Broker Dry-Run Integration

Status: first dry-run adapter slice implemented

Goal:

- connect QuantLab to a real broker API in dry-run style without sending live risk-bearing orders

Scope:

- broker adapter abstraction
- implement `KrakenBrokerAdapter` as the first concrete backend
- dry-run order translation from QuantLab signals
- request/response logging for broker interactions
- idempotency and retry discipline
- broker-side clock/status/preflight validation

Initial slice already present:

- `KrakenBrokerAdapter` behind `BrokerAdapter`
- read-only and validate-only Kraken preflight, account, and dry-run audit surfaces
- read-only Hyperliquid readiness, signing, supervised submit, cancel, and reconciliation surfaces behind the same execution boundary
- canonical session registries and artifact persistence for both broker dry-run and Hyperliquid submit flows

Exit condition:

- QuantLab can build, validate, and log broker-intent orders safely against Kraken without yet operating with live capital

## Stage D.1.b - Second Venue Comparison

Status: initial runtime slices implemented

Goal:

- validate that the execution boundary is real by integrating a second venue with materially different execution semantics

Scope:

- implement a `Hyperliquid` venue adapter behind the existing boundary
- support the venue-specific needs that matter for Hyperliquid-style execution, such as signer-scoped nonces, API/agent wallets, and websocket-driven venue interaction
- compare operational assumptions and abstraction pressure against Kraken
- identify any abstraction leaks that should be fixed in `BrokerAdapter`
- keep `Binance` as optional later comparison work if a second CEX-style contrast still adds value

Before runtime work, a narrow boundary-review slice should clarify the minimal contract support needed for:

- signer identity distinct from execution account
- API / agent wallets
- subaccounts or vault routing
- websocket-first transport preferences

Exit condition:

- QuantLab can support a second materially different venue without moving strategy or risk authority into venue-specific code

## Stage D.2 - Broker Sandbox / Simulated Execution

Status: in progress

Goal:

- test the broker boundary under realistic API conditions before live capital is involved

Scope:

- sandbox or equivalent broker-simulation mode where available
- reconciliation between intended orders and broker responses
- handling partial fills, rejects, rate limits, and transient API failures
- execution-state persistence
- restart/resume behavior

Initial slice already present:

- supervised submit gates, review stubs, and first tightly gated real submit artifacts
- persistent order-status, reconciliation, and supervision artifacts over submitted sessions
- artifact-first health and alert snapshots for Kraken and Hyperliquid submit corridors
- bounded post-submit supervision built around repeated artifacts rather than daemon-first runtime state

Current interpretation:

- `Stage D.2` remains the central QuantLab-owned execution frontier
- it should now be read as a hardening, evidence, and promotion-discipline stage rather than an automatic expansion stage
- the highest-value next steps are evidence-producing and ambiguity-reducing: real artifact runs, tighter runbooks, promotion criteria, and focused fixes on whichever supervised path still fails under realistic use

Exit condition:

- QuantLab can survive operational broker edge cases in a controlled environment

Minimum promotion signals:

- repeated supervised submit sessions can be reconciled without unresolved ambiguous state
- canonical post-submit status and alert artifacts stay current enough to support operator decisions
- restart or resume behavior does not lose pending supervision context for active sessions

## Stage D.3 - Micro-Live Promotion Gate

Status: initial micro-live validation completed; promotion hardening still required

Goal:

- validate the supervised execution stack with minimal real exposure before opening broader supervised live operation

Scope:

- smallest-allowed live sizing and explicit venue or strategy allowlists
- manual promotion checklist from `D.2` hardening into real execution
- canonical secret-boundary discipline for live credentials
- canonical alert coverage for submit, reject, fill, and failure-critical states
- immediate stop-on-ambiguity rule when reconciliation or operator visibility is unclear

Current interpretation:

- D.3 has demonstrated an initial supervised micro-live cycle under bounded exposure
- this does not open Stage E automatically
- the next work is to convert that evidence into repeatability criteria, runbook updates, blocker analysis, alert confidence, reconciliation confidence, and operator stop-control confidence
- no Stage E until D.3 has repeatable evidence, clean alert artifacts, secret-boundary discipline, and operator stop-control confidence

Exit condition:

- QuantLab has passed a bounded micro-live gate with low-risk real sessions, explicit operator review, canonical alert artifacts, and no unresolved promotion blockers around secrets, reconciliation, or stop control

## Stage E - Supervised Live Execution

Status: not started

Goal:

- enable live execution with a human still explicitly supervising the system

Scope:

- live broker credentials under strict safety controls
- manual approval or supervised execution gate
- low-risk initial sizing
- real-time alerts for order placement, rejects, and risk events
- operator dashboard / runbook support through QuantLab artifacts and optional external tooling

Exit condition:

- the system can trade live in a tightly supervised, low-risk mode with full auditability and emergency stop capability

Minimum promotion signals:

- supervised live runs inherit the secret and alert discipline already proven in `D.3`
- operator review, stop control, and auditability remain intact under repeated low-risk live use
- live supervision no longer depends on ad hoc local interpretation to understand order or risk state

## Stage F - Controlled Automation

Status: not started

Goal:

- move from supervised live execution to controlled automation only after paper, safety, broker, and supervised-live layers have proved stable

Scope:

- scheduler / orchestrator-driven recurring execution
- automated decision-to-order flow within approved strategy boundaries
- automated risk gate evaluation before each live action
- post-trade reconciliation and anomaly detection
- automated pause-on-failure behavior
- live performance monitoring against expected risk and drawdown limits

Exit condition:

- QuantLab can operate as an automated broker-connected system with bounded risk, observability, and deterministic stop conditions

## Stage G - Mature Live System

Status: long-term

Goal:

- become a resilient, operator-trustworthy live trading system rather than a research tool with execution attached

Scope:

- stronger portfolio-level capital controls
- multi-strategy deployment governance
- operational incident review workflow
- broker abstraction for additional venues if justified
- formal promotion flow from research -> paper -> supervised live -> automated live

Exit condition:

- strategy promotion, execution, monitoring, and rollback all behave like one coherent operating system rather than a collection of scripts

## Parallel Neural Research Track

Status: proposed — not on the critical path

This track does not replace the main execution and safety roadmap.

It extends QuantLab from a laboratory of explicit strategies into a laboratory of explicit strategies and learned models.

Critical path note:

- Track N is not on the D.2 → D.3 → E critical path
- Track N is a research-discipline expansion, not product repositioning
- No Track N implementation should delay Desktop RC stabilization, D.3 hardening, or supervised execution evidence work
- N.0 may open as documentation/contract work when operational bandwidth allows, but not before the current Desktop + D.3 hardening line is stable

Strategic rule:

- Neural Track = research discipline expansion, not product repositioning
- QuantLab should not be reframed as an AI trading platform
- learned models must meet the same or stricter standards of reproducibility, comparability, auditability, and promotion discipline as rule-based strategies

Authority rule:

- QuantLab owns dataset definition, feature definition, model validation, artifact contracts, and promotion criteria
- maintained local workflows or future optional orchestration tools may later coordinate learned-model workflows, but must not own modeling authority
- Quant Pulse may later provide upstream hypotheses or signal context, but must not certify learned-model validity

### Stage N.0 - Neural Research Foundations

Status: proposed

Goal:

- define the minimum artifact contracts and evaluation discipline needed before learned-model research is implemented

Scope:

- `dataset_manifest.json`
- `feature_manifest.json`
- `model_config.json`
- `training_summary.json`
- temporal split requirements
- random seed discipline
- dataset and feature traceability
- baseline comparison rules
- non-promotion rules

Exit condition:

- QuantLab can describe what a valid learned-model experiment must emit before any training loop, ML dependency, or neural architecture is introduced

See also:

- [learned-model-artifact-contract.md](./learned-model-artifact-contract.md)

### Stage N.1 - Baseline Model Track

Status: proposed, blocked by N.0

Goal:

- introduce classical ML baselines before neural expansion so learned-model claims have a disciplined comparison floor

Scope:

- logistic regression, random forest, gradient boosting, or equivalent baseline models
- temporal targets and horizon definitions
- train / validation / test splits over time
- comparison with existing rule-based baselines
- reporting that combines model metrics and downstream market metrics

Exit condition:

- QuantLab can compare rule-based strategies and classical ML models on the same datasets and temporal splits with canonical outputs

### Stage N.2 - Neural Baseline Support

Status: proposed, blocked by N.0 and N.1

Goal:

- add initial neural architectures only after artifact contracts and ML baselines exist

Scope:

- MLP for tabular features
- GRU/LSTM for simple sequence windows
- reproducible training loops
- regularization and early stopping
- training and validation metric capture
- artifact persistence for model checkpoints and evaluation summaries

Exit condition:

- QuantLab can train, re-evaluate, and compare a simple neural baseline with traceable artifacts and deterministic experiment metadata

### Stage N.3 - Temporal Validation and Market Realism

Status: proposed

Goal:

- evaluate learned models as market systems rather than static predictive exercises

Scope:

- walk-forward validation for models
- leakage checks
- rolling retraining windows
- regime-aware comparison
- score-to-signal translation discipline
- downstream backtest evaluation from model outputs
- out-of-sample comparison against rule-based and ML baselines

Exit condition:

- QuantLab can evaluate learned models under realistic temporal conditions without methodological ambiguity

### Stage N.4 - Model-to-Strategy Translation

Status: proposed

Goal:

- convert learned-model outputs into reviewable research or execution hypotheses instead of opaque score streams

Scope:

- probability or score thresholding
- conviction bands
- regime filters
- horizon mapping
- invalidation conditions for learned strategies
- translation from model output into research actions, paper actions, or bounded draft `ExecutionIntent` candidates

Exit condition:

- learned models produce strategy-relevant, reviewable hypotheses or actions that can be audited and compared like explicit strategies

### Stage N.5 - Paper Promotion for Learned Models

Status: proposed, blocked by N.0 through N.4

Goal:

- allow learned strategies to reach paper mode only under strict comparison and stability discipline

Scope:

- learned-model promotion policy
- required comparison against rule-based and ML baselines
- stability thresholds
- drawdown, turnover, and operational cost gates
- canonical model-risk artifacts
- operator-facing promotion runbook for learned strategies

Exit condition:

- QuantLab can promote a learned strategy into paper trading without weakening its evidence standards or operator review requirements

### Stage N.6 - Orchestrated Neural Research

Status: long-term proposed

Goal:

- allow maintained local workflows or future optional orchestration tools to run learned-model research pipelines while keeping QuantLab as the authority over data, training, validation, and evidence

Scope:

- build-dataset -> train -> validate -> compare -> report workflow chaining
- retries and scheduling for training workflows
- archive and promotion routing
- optional integration with Quant Pulse as an upstream feature or hypothesis source

Exit condition:

- a maintained orchestration path can coordinate learned-model research pipelines while QuantLab remains the canonical owner of experiment definition, evaluation logic, and artifacts

## Recommended Execution Order

From the current operational hardening frontier, the priority order is:

1. Stabilize Desktop / Operator Workspace where it directly supports evidence review, launch continuity, artifact inspection, and Legacy retirement. This is part of the active D.2/D.3 promotion-support path, not a cosmetic track.
2. Harden D.2 / D.3 supervised broker corridors with repeatable evidence, reconciliation, alerts, stop-control, and post-submit clarity.
3. Convert the initial D.3 micro-live evidence into runbook updates, blocker analysis, repeatability criteria, and operator stop-control confidence before any Stage E work.
4. Continue C.1 paper-trading polish only where it strengthens promotion discipline or broker-readiness handoff.
5. Maintain external-consumer contracts only where real integration friction proves a missing producer-side contract. External consumers must not compensate for missing QuantLab contracts.
6. Keep Quant Pulse, broad Numba expansion, and Track N off the active execution-critical path until the current Desktop + D.3 hardening line is stable.
7. Open N.0 only as a documentation/contract track, not implementation, when operational bandwidth allows.
8. Do not open Stage E until D.3 has repeatable evidence, clean alert artifacts, secret-boundary discipline, and operator stop-control confidence.
9. Only after Stage E proves repeated supervised live stability, consider Stage F controlled automation.
10. Avoid reopening Stage D.0 / D.1 as primary stages unless a real hardening gap proves the current boundary insufficient.
11. Continue external-consumer contract and later Stage N.6 work only when real integration or orchestration value justifies them.

## What Should Not Happen Early

- no direct jump from research success to live automated broker execution
- no live broker work before safety limits and kill-switch behavior exist
- no exchange-specific strategy or risk logic outside `BrokerAdapter`
- no expansion of external orchestration before the paper and safety layers are operationally trustworthy
- no new venue or operator-workspace expansion that is disconnected from credible supervised-corridor evidence
- no external orchestration layer becoming QuantLab's product, evidence, or execution authority
- no learned-model promotion before reproducible dataset, feature, and evaluation contracts exist
- no neural-network claims without baseline comparison against explicit strategies and classical ML
- no treating predictive accuracy as sufficient evidence for market usefulness

## Related Documents

- [README.md](../README.md)
- [cli.md](./cli.md)
- [run-artifact-contract.md](./run-artifact-contract.md)
- [learned-model-artifact-contract.md](./learned-model-artifact-contract.md)
- [advantages-and-future.md](./advantages-and-future.md)
- [execution-context-layer.md](./execution-context-layer.md)
- [execution-venue-strategy.md](./execution-venue-strategy.md)
- [hyperliquid-boundary-review.md](./hyperliquid-boundary-review.md)
