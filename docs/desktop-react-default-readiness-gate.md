# React Default-Readiness Gate

## Purpose

Definir el criterio binario y explícito que determina cuándo la shell React de QuantLab Desktop puede convertirse en la shell por defecto, reemplazando a Legacy como interfaz principal del operador.

Este gate separa "paridad funcional técnica" de "default-ready operativo", exigiendo evidencia tanto de CI como de verificación manual.

## Gate Status Definitions

1. **not_ready**: La shell React no ha completado los checks mínimos de funcionalidad o CI.
2. **parity_validated**: Todos los checks de CI pasan y la verificación manual del ciclo operativo completo ha sido exitosa.
3. **default_candidate**: React ha demostrado paridad funcional completa durante un período de uso estable sin regresiones. El operador puede optar por usarla como shell principal.
4. **default_approved**: Se ha ejecutado un PR explícito que activa React como shell por defecto, manteniendo Legacy como fallback.

---

## ✅ Current Gate Status: `default_candidate`

**Declared:** 2026-05-05

React Desktop ha completado todos los checks de CI y la verificación manual del ciclo operativo completo. El operador puede usar React como shell principal. Legacy sigue disponible como rollback.

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
- [x] Legacy sigue disponible como fallback (`npm run start:legacy` funcional)
- [x] No hay errores críticos en la consola del renderer durante el ciclo completo

Verificación manual completada por el operador el 2026-05-05 sobre `main`.

## Known Blockers / Stop Conditions

**Ningún bloqueante activo para el uso de React como default.**

Elementos resueltos antes de la declaración de default_candidate:
- Backend indicator "Offline" cuando servidor activo → resuelto en #516
- Compare muestra error duro en runs huérfanos → resuelto en #519
- Candidates "Open shortlist compare" sin acción → resuelto en #520
- Compare sidebar sin runIds no guiaba al operador → resuelto en #521

**Legacy Status Update (2026-05-05):**
Legacy renderer está oficialmente en modo `deprecated_fallback`. Las funciones de acceso a jobs visibles (Launch jobs, failed jobs) ya fueron migradas a accesos nativos React en #524/#530. Legacy no debe tratarse como verdad arquitectónica.

**Bloqueantes restantes para la eliminación final de Legacy (#529):**
La eliminación final de Legacy solo ocurrirá tras confirmar paridad/contratos nativos:
- Decisión de correlación de run-related jobs (#525), si aún aplica.
- Decisión de necesidad de contrato de backend/producer (#526), si aún aplica.
- Migración de los accesos a sweep decision (#527), si la función sigue activa.

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

## Explicit Non-Goals

- Este gate NO activa React como default.
- Este gate NO retira Legacy.
- Este gate NO modifica código runtime, IPC, backend ni desktop/main.

## Decision Rule for Promoting React to Default

React podrá ser declarado **default_approved** solo cuando:

1. Todos los checks de este documento estén verificados. ✅
2. Exista un PR separado (posterior a este gate) que implemente el cambio de shell por defecto.
3. Ese PR sea revisado y mergeado de forma explícita, no como efecto secundario de otro cambio.

---

## Next Step: `default_approved`

Para promover React a `default_approved`, crear un PR que modifique `desktop/main.js` (o el punto de entrada que selecciona el renderer) para arrancar React en lugar de Legacy por defecto, con Legacy disponible via `npm run start:legacy`. Ese PR debe ser explícito, revisado, y mergeado de forma independiente.
