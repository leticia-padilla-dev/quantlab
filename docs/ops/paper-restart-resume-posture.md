# Paper Restart/Resume Posture (Supervised Operation)

Issue: #721

Status: docs-only posture decision. No runtime changes.

## Objective

Close restart/resume ambiguity for supervised paper operation by making an explicit posture decision that the operator can apply today.

This document governs interpretation of interruptions, stale states, and evidence labeling. It does not implement resume.

## Decision

Path A (Docs-first posture):

- Resume is intentionally unsupported for supervised paper sessions at this stage.
- Restart means a new session id.
- Artifacts and evidence must never be merged across sessions.

Rationale:

- Determinism and auditability are higher priority than convenience.
- A governed “new session on restart” rule reduces accidental evidence corruption.
- Runtime resume can be introduced later only if it preserves artifact integrity and operator clarity.

## Definitions

- Restart: operator launches a new supervised paper session after an interruption or abort.
- Resume: continuing the same session id and artifact lineage after an interruption.
- Stale: a session that appears to have stopped progressing and requires operator classification.
- Aborted: session ended early by operator interruption (e.g., Ctrl+C), not a normal completion.

## Operator Rules (Non-Negotiable)

### Rule 1 — New session id on restart

- After any interruption, the operator must treat the next run as a new session.
- The operator must not overwrite or append artifacts to the prior session.

### Rule 2 — No evidence mixing

- Evidence memos must reference exactly one session id.
- If the operator needs to compare sessions, do it explicitly as comparison, not as merged evidence.

### Rule 3 — Classify first, then proceed

After an interruption or suspicion of stale status:

1. Identify the last session id.
2. Read the session status artifact.
3. Decide classification:
   - completed
   - aborted
   - stale (requires follow-up)
4. Record the classification in a memo.
5. Only then, start a new session if needed.

### Rule 4 — Stale is a stop condition, not an inconvenience

- If a session is stale, stop and classify it.
- Do not “just rerun” without recording the stale condition as evidence.

## Evidence Labeling Rules

Each supervised paper evidence memo must include:

- `session_id`
- `status` (`completed` / `aborted` / `stale`)
- `why` (brief operator rationale)
- `submit_performed: false` (paper only)

## Checklist (Restart / Interruption)

- [ ] I can name the prior `session_id`.
- [ ] I read `session_status.json` for that session.
- [ ] I classified the session (`completed`/`aborted`/`stale`).
- [ ] I wrote a memo referencing only that session.
- [ ] If continuing, I created a new session id and a new memo.

## Runtime Requirements (Future Work, Not Implemented)

If runtime resume is ever implemented, minimum requirements must include:

- Artifact lineage integrity (no mixed partial writes).
- Deterministic resume point with explicit “resume_from” metadata.
- Clear operator-visible differentiation between resumed vs restarted sessions.
- Tests that prove no evidence corruption across interruptions.

## Boundary

- This decision unblocks governance for optional runtime hardening (#722) without requiring that #722 be done.
- Stage E remains blocked.

