# De-Stepbit Migration Inventory

Issue: [#840](https://github.com/leticia-padilla-dev/quantlab/issues/840)
Epic: [#839](https://github.com/leticia-padilla-dev/quantlab/issues/839)

Status: Slice 1 inventory. Documentation and architecture only. No Desktop,
Research UI, IPC, CLI, runtime, service, or test code was changed.

## Canonical Decision

```yaml
canonical_decision:
  initiative: de_stepbit_quantlab
  stepbit_active_architecture: false
  stepbit_active_roadmap: false
  stepbit_active_runtime_dependency: false
  stepbit_future_delivery_commitment: false
  git_history_cleanup_required: false
```

QuantLab must be described as an operator-governed local research and
supervised execution system:

```text
Signals / hypotheses
        ↓
Human operator
        ↓
AI-assisted analysis and planning
        ↓
Local Python workflows
        ↓
QuantLab Core
        ↓
Execution safety boundary
        ↓
Canonical artifacts and evidence
        ↓
Human review
```

Authority model:

```yaml
authority:
  quantlab_core:
    - quantitative_validation
    - execution_engine
    - evidence_generation

  operator:
    - critical_approval
    - risk_limits
    - promotion_authority
    - live_authorization

  ai_assistance:
    - analysis
    - planning
    - code_assistance
    - explanation
    - no_execution_authority

  orchestration:
    current:
      - Python_workflows
    future_options:
      - optional_maintained_orchestration_tool
    mandatory_dependency: false
```

## Migration Success Metric

Do not measure this migration as `grep Stepbit == 0`.

Measure it as:

```yaml
migration_success:
  active_product_reference: 0
  active_runtime_dependency: 0
  active_roadmap_commitment: 0
  visible_user_surface: 0
  unexplained_transitional_identifier: 0
```

## Slice 1 Actions Taken

```yaml
updated:
  - README.md
  - .agents/current-state.md
  - docs/current-state.md
  - docs/roadmap.md
  - docs/architecture/quantlab-system-governance-matrix.md
  - docs/desktop-target-architecture.md
  - docs/architecture/de-stepbit-migration-inventory.md

not_touched:
  - desktop runtime code
  - research_ui runtime code
  - CLI flags
  - IPC channel names
  - service identifiers
  - serialized fields
  - tests
  - contract files
```

## Remaining Reference Classes

### 1. Desktop Runtime And UI

```yaml
classification: preserve_temporarily
risk: high
reason: "Immediate removal affects Electron main/preload/renderer IPC and tests."
files:
  - desktop/main.js
  - desktop/preload.js
  - desktop/main/register-ipc.js
  - desktop/main/config.js
  - desktop/main/ipc-request-path.js
  - desktop/main/stepbit-service.js
  - desktop/shared/ipc/channels.ts
  - desktop/shared/ipc/bridge.ts
  - desktop/shared/models/runtime.ts
  - desktop/renderer/components/SystemPane.tsx
  - desktop/renderer/components/AssistantPane.jsx
  - desktop/renderer/components/QuantLabContext.jsx
  - desktop/renderer/components/PaperOpsPane.tsx
  - desktop/renderer/modules/shell-chrome.js
  - desktop/renderer/modules/tab-renderers.js
  - desktop/README.md
  - desktop/docs/PRODUCT_SURFACES.md
follow_up:
  issue_title: "desktop: remove Stepbit workspace surfaces"
  required_action:
    - remove visible surfaces
    - remove or replace preload APIs
    - remove IPC handlers
    - remove service startup/config
    - update Desktop tests
```

### 2. Research UI Runtime And Controls

```yaml
classification: preserve_temporarily
risk: high
reason: "Immediate removal affects server endpoints, frontend state, visible controls, and tests."
files:
  - research_ui/server.py
  - research_ui/app.js
  - research_ui/index.html
  - research_ui/styles.css
  - research_ui/README.md
follow_up:
  issue_title: "research-ui: remove Stepbit workspace controls"
  required_action:
    - remove endpoints
    - remove start controls
    - remove state cards
    - remove frontend text and buttons
    - update test/test_research_ui_server.py
```

### 3. Contracts, CLI Examples, And Compatibility Fixtures

```yaml
classification: generalize
risk: medium
reason: "The request/signal/report semantics remain useful for external consumers."
files:
  - docs/stepbit-io-v1.md
  - docs/stepbit-local-invocation-contract.md
  - docs/quantlab-stepbit-boundaries.md
  - docs/stepbit-integration.md
  - docs/json-request-contract-verification.md
  - docs/cli.md
  - docs/run-artifact-contract.md
  - src/quantlab/cli/app_args.py
  - test/test_stepbit_external_provider_compat.py
  - test/test_app_cli.py
  - test/test_json_request.py
  - test/test_integration_deterministic.py
  - test/test_machine_sweep_smoke.py
follow_up:
  issue_title: "contracts: generalize Stepbit contracts for external consumers"
  required_action:
    - rename canonical contract language to external_consumer
    - preserve compatibility aliases only where tests require them
    - document alias deprecation
    - update examples away from outputs/stepbit
```

### 4. Active Or Semi-Active Documentation To Reclassify

```yaml
classification: archive_or_generalize
risk: low_to_medium
reason: "Docs may still imply active product surfaces unless marked historical or generalized."
files:
  - docs/advantages-and-future.md
  - docs/use-cases.md
  - docs/brand-guidelines.md
  - docs/research-ui-product-direction.md
  - docs/frontend-integration.md
  - docs/quantlab-desktop-v1.md
  - docs/desktop-v0.1-april-sprint.md
  - docs/desktop-platform-convergence-status.md
  - docs/desktop-platform-convergence-inventory.md
  - docs/desktop-package-lock-policy.md
  - docs/desktop-candidates-shortlist-v1.md
  - docs/workflow-operativo-codex.md
  - docs/v0.1-evidence.md
follow_up:
  issue_title: "docs: archive obsolete Stepbit integration material"
  required_action:
    - mark historical where retained
    - archive obsolete integration plans
    - remove from active navigation/roadmap
```

### 5. Operational Evidence Docs With Negative References

```yaml
classification: preserve_historical_or_negative_reference
risk: low
reason: "Many references explicitly record that no Stepbit work occurred or that Stepbit is forbidden."
examples:
  - docs/ops/stage-e-broker-live-scoping-prerequisites.md
  - docs/ops/stage-e-broker-live-prerequisite-gap-review.md
  - docs/ops/signed-action-roundtrip-validation.md
  - docs/ops/broker-no-submit-evidence-review.md
  - docs/ops/broker-reconciliation-evidence-pack.md
  - docs/ops/paper-live-repeatability-reaudit-after-session-03.md
  - docs/ops/supervised-paper-live-operating-cadence.md
  - docs/ops/supervised-paper-readiness-audit.md
follow_up:
  issue_title: "docs: archive obsolete Stepbit integration material"
  required_action:
    - preserve audit history where useful
    - do not rewrite historical evidence unless it implies active architecture
```

### 6. Landing / Public Page References

```yaml
classification: update_later
risk: medium
reason: "Visible product copy should not present Stepbit as optional active product layer."
files:
  - landing/index.html
follow_up:
  issue_title: "web: remove Stepbit from public product copy"
  required_action:
    - remove visible Stepbit layer/tag
    - preserve current QuantLab positioning
```

## Transitional Technical Identifiers Intentionally Preserved

These names remain only to avoid unsafe removal in Slice 1:

```yaml
identifiers:
  ipc:
    - quantlab:ask-stepbit-chat
    - /api/stepbit-workspace/start
    - /api/stepbit-workspace
  services:
    - createStepbitService
    - stepbit-service.js
  config:
    - STEPBIT_APP_ROOT
    - STEPBIT_APP_CONFIG_PATH
  tests:
    - test_stepbit_external_provider_compat.py
    - test_build_stepbit_workspace_payload_detects_local_repos
    - test_start_stepbit_workspace_starts_missing_services
  docs:
    - stepbit-io-v1.md
    - stepbit-local-invocation-contract.md
    - quantlab-stepbit-boundaries.md
```

Each transitional identifier requires a dedicated migration or deletion issue.
They must not be interpreted as current architecture.

## Next Slices

```yaml
next_slices:
  2:
    title: "desktop: remove Stepbit workspace surfaces"
    type: code_and_tests

  3:
    title: "research-ui: remove Stepbit workspace controls"
    type: code_and_tests

  4:
    title: "contracts: generalize Stepbit contracts for external consumers"
    type: docs_code_tests

  5:
    title: "docs: archive obsolete Stepbit integration material"
    type: docs_only

  final:
    title: "audit: verify de-stepbit migration completion"
    type: audit
```

## Slice 1 Decision

```yaml
decision:
  stepbit_active_architecture: false
  stepbit_active_roadmap: false
  stepbit_runtime_references:
    status: transitional_inventory_created
  stepbit_contract_references:
    status: pending_generalization
  stepbit_visible_surfaces:
    status: pending_desktop_and_research_ui_slices
```
