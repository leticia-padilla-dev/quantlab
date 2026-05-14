# Paper: Operational Repeatability vs Market Robustness

Issue: [#755](https://github.com/Whiteks1/quantlab/issues/755)

Status: docs-only. No runtime changes. No submit. Stage E remains blocked.

## Purpose

Define two different claims that are often accidentally conflated:

- operational_repeatability: "Operators can run paper sessions and reach the same deterministic conclusions from artifacts."
- market_robustness: "A strategy behaves acceptably across different market windows and regimes."

QuantLab must keep these separate. Passing operational repeatability does not imply market robustness.

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Definitions

### Operational Repeatability (Paper)

Operational repeatability is satisfied only when the paper corridor is:

- artifact-complete: the canonical session pack exists and is navigable
- interpretation-deterministic: two operators reading the same artifacts reach the same terminal classification
- stop-governed: ambiguity produces stop, not "keep trying"
- runbook-driven: no hidden context (console logs, screenshots, memory) is required to classify outcomes

This is an operational property of QuantLab as a system, not a performance claim about strategies.

### Market Robustness (Research/Evaluation)

Market robustness is satisfied only when a strategy exhibits bounded behavior across:

- different market windows
- different volatility / regime conditions
- different liquidity / spread contexts

This is a statistical property. It depends on evaluation methodology, not just artifact discipline.

## What Repeatability Can and Cannot Claim

```yaml
operational_repeatability:
  can_claim:
    - "The paper session pipeline is operable and audit-friendly."
    - "Artifacts support deterministic operator conclusions."
    - "Stop rules prevent hidden runtime widening."
  cannot_claim:
    - "The strategy is profitable."
    - "The strategy is robust to market regime change."
    - "The system is ready for broker-connected execution."

market_robustness:
  can_claim:
    - "Behavior is bounded across multiple market windows."
    - "Variance is acceptable under defined evaluation criteria."
  cannot_claim:
    - "Operator discipline exists."
    - "Runtime/observability contracts are clear."
```

## Evidence Requirements (Operational Repeatability)

Minimum evidence for a paper session to be considered repeatable-operable:

```yaml
paper_session_artifacts:
  root: "outputs/paper_sessions/<session_id>/"
  required:
    - session_metadata.json
    - session_status.json
    - report.json
    - trades.csv
  recommended:
    - config.json
    - metrics.json
    - run_report.md

interpretation:
  required:
    - "A deterministic terminal classification (terminal vs non_terminal)."
    - "A deterministic severity classification (ok / warning / critical)."
    - "A deterministic operator action (continue evidence capture vs stop)."
```

## Evidence Requirements (Market Robustness)

Market robustness must be proven with an explicit evaluation protocol (not by running one paper session repeatedly).

Minimum evidence shape:

```yaml
robustness_evidence:
  requires:
    - "Multiple market windows / regimes."
    - "Explicit metrics and acceptable variance bounds."
    - "A clear definition of failure modes (drawdown, churn, false positives, etc.)."
  must_not_depend_on:
    - "Operator memory."
    - "Ad hoc story justification."
    - "Single-run anecdotes."
```

## Non-Goals

- This document does not authorize broker actions.
- This document does not authorize submit retries.
- This document does not open Stage E.
- This document does not define strategy selection or risk policy.
