# Current State - QuantLab

**Date:** 2026-04-30
**Purpose:** stable operational snapshot of the QuantLab repo

## Operational Posture

QuantLab is operating as an **advanced operational RC**: the core engine is mature, the CLI and machine-facing contracts are stable, and the remaining work is concentrated on execution-safety evidence, operator visibility, and Desktop RC hardening.

The repository does **not** need a new base architecture layer. The current frontier is the operational contract between **D.2** and **D.3**.

## Current System Shape

- **QuantLab Core**: quantitative validation and evidence authority
- **Desktop**: operator workspace and review surface
- **Stepbit**: orchestration/control plane only, not QuantLab authority
- **Quant Pulse**: upstream signal and hypothesis layer only

## Stage Status

- **Core engine**: mature
- **CLI / machine contracts**: stable
- **Desktop workspace**: v0.1 RC, active and not yet fully closed
- **Stage D.2**: closed-in-code, under evidence hardening
- **Stage D.3**: next real frontier, gated by explicit promotion criteria
- **Live automated execution**: not ready

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

- Stepbit adapter and orchestration
- Quant Pulse intake
- broader venue expansion
- neural research track
- controlled automation

## Operating Principles

- QuantLab validates; Stepbit orchestrates
- Quant Pulse proposes signals; QuantLab decides what is worth testing
- Desktop reduces operator ambiguity; it does not become a second source of authority
- no move from implemented to live without auditable evidence
- any D.3 promotion must be explicit, binary, and traceable

## Maintenance Rule

This file is a curated operational snapshot, not a live Git inventory.

It should be updated when repo-level priorities or stage posture change materially.
