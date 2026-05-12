# Epistemic UI Guardrails (QuantLab Desktop)

QuantLab Desktop is an operator evidence-review instrument.
The UI must serve evidence, not compete with it.

## Core principle

visual_quality != epistemic_quality

A UI can look modern and still:
- exaggerate confidence
- hide uncertainty
- introduce accidental semantics
- distort readiness

## UI as evidence transport

UI should:
- preserve evidence fidelity
- reduce interpretation ambiguity
- expose uncertainty explicitly
- maintain traceability between claim and evidence

UI should not:
- manufacture confidence
- compress nuanced evidence into simplistic states
- hide unresolved uncertainty

## Threat model (what we are protecting)

Failure modes we actively avoid:
- implicit authority (UI implies certainty the system does not have)
- visual overconfidence ("green means safe")
- accidental semantics (layout/state suggests automation)
- operator continuity break (cognitive retraining cost)
- surface expansion ("since we touched UI..." cascade)
- hidden coupling (UI changes force behavioral changes)

## Guardrails

### 1) No hidden semantics

UI changes must not:
- introduce new authority
- imply automation not present
- visually exaggerate confidence/readiness

Examples:
- A big green "READY" badge can imply deployment confidence.
- An animation or celebratory state can imply automated approval.
- Rankings can imply scoring authority.

Allowed alternative:
- Use precise language tied to evidence:
  - "Passed current validation filters"
  - "Meets promotion criteria X/Y/Z (see evidence)"
  - "Confidence: unknown / not evaluated"

### 2) Operator continuity over aesthetic consistency

When in conflict:
operator_continuity > aesthetic_consistency

Rules of thumb:
- Preserve recognized anchors (labels, placement, key affordances) unless ambiguity is reduced by changing them.
- Prefer additive clarity over rearranging the mental map.
- If a change requires retraining, it must buy measurable ambiguity reduction.

### 3) Every slice must reduce ambiguity

A UI slice is acceptable only if it improves at least one:
- visibility
- consistency
- traceability
- confidence correctness (not just "more confidence")
- cognitive clarity

If it improves none: it does not ship.

## Confidence signaling rules

- Never use "certainty language" unless evidence supports it.
- Prefer explicit uncertainty over implied certainty.
- Avoid single-signal readiness; if readiness exists, show criteria + links to evidence.
- Colors are not truth.
  - Color may summarize, but must not replace explanation.

## Authority boundaries

Desktop is a read-only operator workspace.
It must not become a second execution authority.

UI must not:
- trigger live actions without explicit user approval
- suggest broker authority
- imply automated promotion/execution

## PR / Slice checklist (required for UI-facing changes)

## Epistemic / Operator Review

### What ambiguity does this reduce?
- ...

### What implicit authority could this introduce?
- ...

### How is that authority constrained or avoided?
- ...

### What operator continuity is preserved?
- ...

### Could this visually exaggerate confidence/readiness?
- yes/no
- mitigation:
