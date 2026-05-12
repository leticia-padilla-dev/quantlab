# Desktop Design Canon (QuantLab)

This document defines the canonical design direction for QuantLab Desktop.
It is intentionally concise so that implementation slices can follow it without reinterpreting the Claude Design prototypes.

## Canon vs reference

Canon is:
- The semantic product constraints (operator workspace, evidence-first, authority boundaries).
- The UX governance rules (epistemic guardrails).
- The visual direction at the level of principles (not pixel specs).
- The surface hierarchy and implementation order.

Reference is:
- `desktop/docs/design/claude-design-evolution/` — Claude Design Desktop prototypes and token/surface sketches (visual/UX reference only).
- `desktop/docs/design/claude-mobile-companion/` — mobile companion concept reference (boundary definition exercise; not an implementation plan).

Reference material must not be copied wholesale into production code.

## Product stance

QuantLab Desktop is a read-only operator evidence-review workspace.
It must not become a second execution authority.

## Mandatory guardrails

All UI-facing slices must follow:
- `desktop/docs/design/epistemic-ui-guardrails.md`

Operationally:
- No hidden semantics (no implied authority, automation, or confidence exaggeration).
- Operator continuity over aesthetic consistency.
- Every slice must reduce ambiguity (visibility / traceability / consistency / cognitive clarity).

## Visual direction (principles)

- Dark analytical instrument, not a consumer app.
- Density is allowed when it improves scanability and evidence clarity.
- Motion is optional and must never imply automation or certainty.
- Color may summarize, but must not replace explanation.

## Evidence-first hierarchy

Primary hierarchy should make evidence legible and attributable:
- Claims must be traceable to artifacts, reports, and lineage.
- Uncertainty and missing evidence must be explicit, not hidden.
- “Readiness” must be decomposed into criteria with evidence links.

## Token principles

Token convergence exists to reduce drift and preserve continuity:
- Prefer a minimal vocabulary (color, spacing, typography, surfaces).
- Prefer additive alignment over large refactors.
- Tokens are a contract: avoid one-off CSS that creates semantic mismatch.

## Surface hierarchy

Desktop surfaces are operator instruments:
- Runs: discovery and selection context
- Run detail: evidence workspace (artifacts, verdicts, lineage)
- Compare: decision-oriented comparison workspace
- Candidates: local decision memory (baseline/shortlist/notes)
- Experiments: configuration and sweep visibility
- System / Paper Ops / Launch: operational context and continuity

## Authority boundaries

Desktop must not:
- submit live orders
- promote automatically
- imply broker authority
- imply scoring authority not backed by evidence

## Implementation order (incremental)

Implementation is slice-based and contract-preserving.
No big-bang redesign.

1) Shell/runtime convergence
2) Token vocabulary convergence
3) Status strip (runtime + corridor + continuity signals)
4) Evidence lineage visibility (rail, traceability)
5) Compare refinements (research-oriented comparison)
6) Store migration slices only if contract-preserving (keep QuantLabContext operational API stable until callers migrate)
