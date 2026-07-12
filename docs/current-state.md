# Current State - QuantLab

**Date:** 2026-07-12
**Purpose:** stable operational snapshot of the QuantLab repo

## Operational Posture

QuantLab is operating as an **advanced operational RC**: the core engine is mature, the CLI and machine-facing contracts are stable, and the remaining work is concentrated on execution-safety evidence, operator visibility, and Desktop RC hardening.

The repository does **not** need a new base architecture layer. The current frontier is the operational contract between **D.2** and **D.3**.

## Current System Shape

- **QuantLab Core**: quantitative validation and evidence authority
- **Desktop**: operator workspace and review surface
- **Local Python workflows / maintained external-consumer contracts**: optional invocation boundary only, not product authority
- **Quant Pulse**: upstream signal and hypothesis layer only

## Stage Status

- **Core engine**: mature
- **CLI / machine contracts**: stable
- **Desktop workspace**: v0.1 RC, active and not yet fully closed
- **Stage D.2**: closed-in-code, under evidence hardening
- **Stage D.3**: next real frontier, gated by explicit promotion criteria
- **Live automated execution**: not ready

## Desktop Native Hydration Completion

The `#410` native hydration track is complete as of `09c8801`:

- Run Detail completed through `#501`
- Paper Ops and System completed through `#503`
- Experiments completed through a documented direct-main exception

The direct-main completion is a traceability exception only. It is not a
precedent for future Desktop work. Future Desktop changes must start from a
fresh `main` branch and go through PR review.

## Active Promotion Path

The current execution path is sequential, not parallel:

1. Desktop RC stabilization
2. D.3 promotion gate definition
3. D.2 evidence pack production
4. signed-action / allowlist enforcement
5. single supervised micro-live validation

Only after that sequence should the repo move into:

6. Desktop legacy cleanup
7. research quality closure

## Deferred Tracks

These tracks remain outside the current critical path:

- Quant Pulse intake
- broader venue expansion
- neural research track
- controlled automation

Stepbit has been retired from the active QuantLab architecture. Existing
Stepbit-specific runtime identifiers, UI surfaces, docs, and test fixtures are
transitional until migrated through dedicated de-stepbit slices. They must not
be interpreted as current product architecture, roadmap commitment, or future
dependency.

## Operating Principles

- QuantLab Core owns quantitative validation, execution semantics, and evidence generation
- the human operator owns critical approval, risk limits, promotion authority, and live authorization
- AI assistance may support analysis, planning, code assistance, and explanation, but has no execution authority
- local Python workflows are the current lightweight orchestration baseline; future orchestration tools are optional, not mandatory dependencies
- Quant Pulse proposes signals; QuantLab decides what is worth testing
- Desktop reduces operator ambiguity; it does not become a second source of authority
- no move from implemented to live without auditable evidence
- any D.3 promotion must be explicit, binary, and traceable

## Maintenance Rule

This file is a curated operational snapshot, not a live Git inventory.

It should be updated when repo-level priorities or stage posture change materially.
