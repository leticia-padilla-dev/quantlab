# React Default-Readiness Gate

## Purpose

Definir el criterio binario y explícito que determina cuándo la shell React de QuantLab Desktop puede convertirse en la shell por defecto, reemplazando a Legacy como interfaz principal del operador.

Este gate separa "paridad funcional técnica" de "default-ready operativo", exigiendo evidencia tanto de CI como de verificación manual.

## Gate Status Definitions

1. **not_ready**: La shell React no ha completado los checks mínimos de funcionalidad o CI.
2. **parity_validated**: Todos los checks de CI pasan y la verificación manual del ciclo operativo completo ha sido exitosa.
3. **default_candidate**: React ha demostrado paridad funcional completa durante un período de uso estable sin regresiones. El operador puede optar por usarla como shell principal.
4. **default_approved**: Se ha ejecutado un PR explícito que activa React como shell por defecto, manteniendo Legacy como fallback.

## Required CI Checks

- [ ] `npm run typecheck`
- [ ] `npm run build`
- [ ] `npm run smoke:react:fallback`
- [ ] `npm run smoke:react:real-path`
- [ ] `npm run smoke:legacy:fallback`
- [ ] Todos los checks de GitHub Actions pasan en `main`

## Required Manual Operator Checks

- [ ] `start-react-dev.ps1` arranca React correctamente con backend e índice de runs
- [ ] Backend indicator muestra "Online" cuando el servidor está activo y "Offline" cuando no
- [ ] Launch permite seleccionar una configuración existente del dropdown y ejecutar un sweep con éxito
- [ ] Runs muestra los runs indexados existentes y los nuevos generados tras un sweep
- [ ] Open run / Artifacts es accesible y muestra datos correctos por cada run
- [ ] Mark candidate funciona y la superficie Candidates refleja el estado actualizado
- [ ] Compare funciona con al menos 2 runs seleccionados y muestra métricas comparativas
- [ ] Legacy sigue disponible como fallback (`npm run start:legacy` funcional)
- [ ] No hay errores críticos en la consola del renderer durante el ciclo completo

## Known Blockers / Stop Conditions

- El indicador de backend muestra "Offline" cuando el servidor está activo (corregido en #516, requiere verificación post-merge).
- Cualquier smoke o check de CI que falle en `main`.
- Cualquier paso del ciclo operativo que no pueda completarse exclusivamente desde React.

## Evidence Required

- Capturas de pantalla o logs de cada paso del ciclo operativo manual completado en React.
- Resultados de CI en verde en la rama `main` tras el merge de todos los PRs habilitadores.
- Confirmación escrita del operador de que el ciclo completo fue exitoso.

## Enabling Slices (PRs)

- #507: bridge sweep decision actions
- #508: own candidates store
- #509: operator recovery actions for empty runs
- #510: launch config selector
- #511: surface diagnostics
- #514: React dev start helper
- #516: fix backend status indicator

## Explicit Non-Goals

- Este gate NO activa React como default.
- Este gate NO retira Legacy.
- Este gate NO modifica código runtime, IPC, backend ni desktop/main.

## Decision Rule for Promoting React to Default

React podrá ser declarado **default_approved** solo cuando:

1. Todos los checks de este documento estén verificados.
2. Exista un PR separado (posterior a este gate) que implemente el cambio de shell por defecto.
3. Ese PR sea revisado y mergeado de forma explícita, no como efecto secundario de otro cambio.
