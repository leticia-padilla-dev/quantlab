# Desktop Token Vocabulary Drift — Inventory

## Objective

Make current token vocabulary drift explicit (canonical vs legacy) before any migration work.

## Scope

- Inventory duplicated/inconsistent token vocabularies
- Document canonical candidates vs legacy usage
- Identify drift hotspots (files/sections)

## Out of scope

- No runtime changes
- No renderer behavior changes
- No CSS/token implementation changes
- No Zustand/store changes
- No QuantLabContext API changes

## Token vocabularies found

### A) Runtime CSS variables (active) — `--bg/*` family

Defined in `desktop/renderer/styles.css` under `:root` and imported by `desktop/renderer/src/App.tsx`.

Primary surface/text tokens:
- `--bg`, `--bg-soft`, `--bg-panel`, `--bg-hover`
- `--border`, `--border-strong`
- `--text`, `--muted`
- `--accent`, `--accent-signal`
- `--warning`, `--danger`, `--success`

Derived/alias tokens:
- Surface aliases: `--surface-base`, `--surface-panel`, `--surface-card`, `--surface-elevated`
- Status backgrounds: `--status-success-bg`, `--status-warning-bg`, `--status-danger-bg`

Notes:
- This vocabulary is internally coherent and is what currently provides most of the visible styling.
- It includes both semantic tokens (`--success/*`) and “palette-ish” helpers (`--blue-*`, `--accent-rgb`).

### B) Pane CSS variables (expected but undefined) — `--color-*` family

Referenced in pane CSS files but not defined anywhere in runtime CSS.

Where it is referenced:
- `desktop/renderer/components/RunsPane.css`
- `desktop/renderer/components/CandidatesPane.css`
- `desktop/renderer/components/ComparePane.css`

Representative tokens used:
- Surfaces: `--color-surface`, `--color-surface-2`, `--color-panel-bg`
- Text: `--color-text-primary`, `--color-text-secondary`, `--color-muted`
- Lines: `--color-border`
- Semantics: `--color-positive`, `--color-warning`, `--color-danger`, `--color-negative`, `--color-info`
- Accent: `--color-accent`

Notes:
- In pure CSS usage (no fallback), undefined variables yield “missing styling” risk (transparent backgrounds, missing borders, etc.).
- In JSX inline styles, some uses include fallbacks, e.g. `desktop/renderer/components/AssistantPane.jsx` uses `var(--color-*, <hex>)`.

### C) Canonical candidate token system (documented) — `--ink/*`, `--line/*`, `--s-*` family

Defined in `desktop/docs/design/claude-design-evolution/tokens.css` (design reference).

Key properties:
- Single palette + surface scale: `--ink-900..650`
- Lines: `--line-soft`, `--line`, `--line-strong`, `--line-rail`
- Text: `--text`, `--text-soft`, `--muted`, `--muted-dark`
- Accent: `--accent`, `--accent-soft`, `--accent-line`
- Semantics: `--success|--warn|--danger|--info` (+ `*-bg`)
- Spacing/radius/density: `--s-*`, `--r-*`, `--row-h`, `--pad-pane`

Notes:
- This is explicitly documented as the “single canonical palette”, replacing the two competing systems (A and B).
- It is currently reference-only; it is not imported by the Desktop runtime.

### D) CSS module legacy vocabulary (likely inactive) — `.shell { --bg/* }`

Defined in `desktop/renderer/src/App.module.css` as scoped variables under `.shell`.

Notes:
- `App.module.css` is not currently imported anywhere in the renderer codebase.
- This means its token definitions should be treated as legacy drift until proven otherwise.

## Drift hotspots (files)

- Runtime token source: `desktop/renderer/styles.css`
- `--color-*` expectations without a definition:
  - `desktop/renderer/components/RunsPane.css`
  - `desktop/renderer/components/CandidatesPane.css`
  - `desktop/renderer/components/ComparePane.css`
- Inline fallbacks that “mask” missing `--color-*` in some cases:
  - `desktop/renderer/components/AssistantPane.jsx`
- Legacy scoped token definition (currently unreferenced):
  - `desktop/renderer/src/App.module.css`
- Canonical palette candidate (design reference):
  - `desktop/docs/design/claude-design-evolution/tokens.css`

## Vocabulary collisions / mismatches

- Status naming drift:
  - Runtime uses `--warning`; canonical candidate uses `--warn`.
  - Pane CSS expects `--color-warning` and `--color-positive`, while runtime uses `--success`.
- Surface naming drift:
  - Runtime uses `--bg/*` and `--surface-*` aliases.
  - Canonical candidate uses `--ink-*`.
  - Pane CSS expects `--color-surface`, `--color-panel-bg`.
- Text naming drift:
  - Runtime uses `--text`, `--muted`.
  - Pane CSS expects `--color-text-primary`, `--color-text-secondary`, `--color-muted`.

## Intended follow-up slices (non-binding)

This inventory is designed to enable the next incremental slices for #686:
- S2: introduce canonical desktop token constants (choose a single vocabulary and document mappings)
- S3: migrate token usage to canonical constants (lowest-risk, surface-by-surface)
- S4: align smoke fallback assertions with canonical tokens
