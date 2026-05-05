# React Default-Readiness Gate

## Purpose

Definir el criterio binario y explícito que determina cuándo la shell React de QuantLab Desktop puede convertirse en la shell por defecto, reemplazando a Legacy como interfaz principal del operador.

Este gate separa "paridad funcional técnica" de "default-ready operativo", exigiendo evidencia tanto de CI como de verificación manual.

## Gate Status Definitions

1. **not_ready**: La shell React no ha completado los checks mínimos de funcionalidad o CI.
2. **parity_validated**: Todos los checks de CI pasan y la verificación manual del ciclo operativo completo ha sido exitosa.
3. **default_candidate**: React ha demostrado paridad funcional completa durante un período de uso estable sin regresiones. El operador puede optar por usarla como shell principal.
4. **default_approved**: React es el único renderer. El Legacy renderer ha sido eliminado. El rollback ya no es posible vía switch de entorno; requiere revertir desde Git history.

---

## ✅ Current Gate Status: `default_approved`

**Declared:** 2026-05-05
**Legacy removal completed:** 2026-05-05 (PR #539 / Issue #529)

React Desktop es el único renderer de QuantLab. El Legacy renderer fue eliminado tras confirmar paridad nativa completa. No existe rollback vía `start:legacy` ni `QUANTLAB_DESKTOP_RENDERER`; el rollback requiere revertir o restaurar desde Git history.

---

## Required CI Checks

- [x] `npm run typecheck`
- [x] `npm run build`
- [x] `npm run smoke:react:fallback`
- [x] `npm run smoke:react:real-path`
- [x] `npm run smoke:legacy:fallback`
- [x] Todos los checks de GitHub Actions pasan en `main`

Todos los checks verificados en los PRs habilitadores (#507–#521). CI verde en `main` en `0fbbcde`.

## Required Manual Operator Checks

- [x] `start-react-dev.ps1` arranca React correctamente con backend e índice de runs
- [x] Backend indicator muestra "Online" cuando el servidor está activo y "Offline" cuando no
- [x] Launch permite seleccionar una configuración existente del dropdown y ejecutar un sweep con éxito
- [x] Runs muestra los runs indexados existentes y los nuevos generados tras un sweep
- [x] Open run / Artifacts es accesible y muestra datos correctos por cada run
- [x] Mark candidate funciona y la superficie Candidates refleja el estado actualizado
- [x] Compare funciona con al menos 2 runs seleccionados y muestra métricas comparativas
- [x] Legacy estaba disponible como fallback durante la fase `default_candidate` (`npm run start:legacy` funcional)
- [x] No hay errores críticos en la consola del renderer durante el ciclo completo

Verificación manual completada por el operador el 2026-05-05 sobre `main`.

## Known Blockers / Stop Conditions

**Ningún bloqueante activo para el uso de React como default.**

Elementos resueltos antes de la declaración de default_candidate:
- Backend indicator "Offline" cuando servidor activo → resuelto en #516
- Compare muestra error duro en runs huérfanos → resuelto en #519
- Candidates "Open shortlist compare" sin acción → resuelto en #520
- Compare sidebar sin runIds no guiaba al operador → resuelto en #521

**Legacy Removal (2026-05-05) — PR #539 / Issue #529:**
El Legacy renderer fue eliminado tras confirmar paridad nativa completa:
- Jobs accessors nativos: #530 (getJobs, getLatestFailedJob, getRunRelatedJobs, findJob)
- Sweep decision store nativo: #527
- `smoke:fallback` pasa sin Legacy cargado ✅
- `npm run typecheck` ✅ · `npm run build` ✅ · `git status` limpio ✅

No existe rollback de runtime. Rollback requiere `git revert` o restauración desde Git history.

## Evidence Required

- Verificación manual del ciclo operativo completo (Launch → Runs → Candidates → Compare → Artifacts) confirmada por el operador el 2026-05-05.
- CI verde en todos los PRs habilitadores. `main` en `0fbbcde` limpio.
- Ningún crash ni error crítico de consola reportado durante el ciclo completo.

## Enabling Slices (PRs)

**Paridad funcional base:**
- #501: native run detail hydration (`useRunDetail`)
- #503: native snapshot hydration para Paper Ops + System (`useSnapshot`)
- #507: bridge sweep decision actions en QuantLabContext
- #508: candidates store nativo (`useCandidatesStore`)
- #509: operator recovery actions para empty runs state
- #510: launch config selector
- #511: surface diagnostics (backend/index en System, Runs, Launch)

**Tooling y cierre de gaps:**
- #512: dev start helper Legacy
- #513: refresh manual de runs en RunsPane
- #514: dev start helper React (`start-react-dev.ps1`)
- #515: docs functional parity evidence
- #516: fix backend status indicator
- #517: docs readiness gate (este documento)
- #518: health poll del backend para live diagnostics
- #519: Compare stale-run graceful recovery + auto-poda
- #520: wire Candidates → Compare y Baseline
- #521: Compare context-aware desde sidebar (empty state guiado)

## Enabling Slices — Legacy Retirement Completion

**Native replacement (post-candidate):**
- #524/#530: native jobs accessors (getJobs, getLatestFailedJob, getRunRelatedJobs, findJob)
- #527: native sweep decision store (useSweepDecisionStore)
- #528: docs deprecated-fallback step
- #529/PR #539: Legacy renderer removal

## Final State

Gate `default_approved` confirmed. React is the sole Desktop renderer. `window.quantlabDesktop` / preload / IPC are unaffected by Legacy removal — they remain the stable operator-to-backend contract.

---

## Next Step: `default_approved`

Para promover React a `default_approved`, crear un PR que modifique `desktop/main.js` (o el punto de entrada que selecciona el renderer) para arrancar React en lugar de Legacy por defecto, con Legacy disponible via `npm run start:legacy`. Ese PR debe ser explícito, revisado, y mergeado de forma independiente.
