# Desktop Runtime Token Contract — Canonical v1

## Goal

Stabilize the runtime token *name* contract without redesigning the palette.

## Runtime canonical v1

Defined in `desktop/renderer/styles.css` under `:root`:
- Surfaces: `--bg`, `--bg-soft`, `--bg-panel`, `--bg-hover`
- Lines: `--border`, `--border-strong`
- Text: `--text`, `--muted`
- Accent: `--accent`, `--accent-signal`
- Semantics: `--success`, `--warning`, `--danger`

## Legacy aliases (supported)

These aliases exist to keep legacy pane CSS stable until surface-by-surface migration:

| Legacy token | Resolves to |
| --- | --- |
| `--color-surface` | `--bg-soft` |
| `--color-surface-2` | `--bg-hover` |
| `--color-panel-bg` | `--bg-panel` |
| `--color-border` | `--border` |
| `--color-text-primary` | `--text` |
| `--color-text-secondary` | `--muted` |
| `--color-muted` | `--muted` |
| `--color-accent` | `--accent` |
| `--color-positive` | `--success` |
| `--color-warning` | `--warning` |
| `--color-danger` | `--danger` |
| `--color-negative` | `--danger` |
| `--color-info` | `--accent-signal` |

## Note on design reference tokens

`desktop/docs/design/claude-design-evolution/tokens.css` (`--ink-*`, `--line-*`) is direction/reference, not a runtime contract for v1.

