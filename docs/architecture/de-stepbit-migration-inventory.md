# De-Stepbit Migration Inventory

Issue: [#840](https://github.com/leticia-padilla-dev/quantlab/issues/840)
Epic: [#839](https://github.com/leticia-padilla-dev/quantlab/issues/839)

Status: Slice 1 inventory plus Slice 2 Desktop and Slice 3 Research UI
completion records. CLI, contracts, Core runtime, and compatibility tests remain
assigned to later slices.

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

## Slice 2 Desktop Actions Taken

```yaml
desktop_slice:
  issue: 842
  pr: 843
  merge_commit: 127c48228466e8f4914a431f5f48d96438828ce4
  status: completed

  removed:
    - visible_workspace_surfaces
    - assistant_adapter
    - preload_bridge_API
    - IPC_channel
    - IPC_handler
    - stepbit_service
    - STEPBIT_configuration
    - runtime_status_fields
    - renderer_actions_and_copy

  residual_stepbit_identifiers_in_desktop: []

  validation:
    typecheck: pass
    build: pass
    smoke_fallback: pass
    smoke_real_path: pass
    CI: pass
    reference_search: zero_matches

  tests:
    modified: false
    justification: "Existing Desktop typecheck, build, fallback smoke, and real-path smoke exercised the affected startup, preload, IPC, and renderer paths."
```

Slice 2 deliberately did not edit `research_ui`, CLI contracts, Python code,
or Python tests. Those remain assigned to later slices.

## Slice 3 Research UI Actions Taken

```yaml
research_ui_slice:
  issue: 846
  pr: 847
  status: completed

  removed:
    - visible_workspace_controls
    - frontend_state_and_fetches
    - workspace_state_cards
    - start_buttons_and_open_links
    - /api/stepbit-workspace
    - /api/stepbit-workspace/start
    - server_workspace_payload_builder
    - server_start_helper
    - start_state_and_live_url_detection
    - research_ui_stepbit_tests
    - research_ui_stepbit_readme_copy

  residual_stepbit_identifiers_in_research_ui: []

  validation:
    targeted_research_ui_tests: pass
    server_compile: pass
    startup_smoke: pass
    reference_search: zero_matches
```

Slice 3 deliberately did not edit Desktop, Core, CLI/json-request contracts,
or provider compatibility contracts. Those remain assigned to later slices.

## Remaining Reference Classes

### 1. Desktop Runtime And UI

```yaml
classification: removed
risk: closed_for_desktop
reason: "PR #843 removed Desktop-side visible surfaces, bridge/API, IPC, service, config, and renderer copy."
issue: 842
pr: 843
residual_identifiers: []
validated_by:
  - "cd desktop && npm run typecheck"
  - "cd desktop && npm run build"
  - "cd desktop && npm run smoke:fallback"
  - "cd desktop && npm run smoke:real-path"
  - "rg Stepbit/stepbit patterns under desktop returned zero matches"
follow_up:
  status: complete
  note: "No Desktop-specific follow-up remains in this inventory."
```

### 2. Research UI Runtime And Controls

```yaml
classification: removed
risk: closed_for_research_ui
reason: "Slice 3 removed Research UI visible controls, frontend state, fetches, endpoints, start helpers, and targeted tests."
files:
  - research_ui/server.py
  - research_ui/app.js
  - research_ui/index.html
  - research_ui/styles.css
  - research_ui/README.md
  - test/test_research_ui_server.py
issue: 846
residual_identifiers: []
validated_by:
  - "python -m py_compile research_ui/server.py"
  - "python -m pytest -q test/test_research_ui_server.py"
  - "Research UI startup smoke"
  - "rg Stepbit/stepbit patterns under research_ui and test/test_research_ui_server.py returned zero matches"
follow_up:
  status: complete
  note: "No Research UI-specific follow-up remains in this inventory."
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
  - docs/desktop-target-architecture.md
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

These names remain outside the completed Desktop slice and require later
dedicated migration or deletion work:

```yaml
identifiers:
  tests:
    - test_stepbit_external_provider_compat.py
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
    status: completed
    issue: 842
    pr: 843

  3:
    title: "research-ui: remove Stepbit workspace controls"
    type: code_and_tests
    status: completed
    issue: 846
    pr: 847

  4:
    title: "contracts: generalize Stepbit contracts for external consumers"
    type: docs_code_tests
    status: in_progress
    issue: 848
    generalized:
      - New canonical docs: docs/external-consumer-io-v1.md and docs/external-consumer-local-invocation-contract.md
      - Updated CLI help text for --json-request to refer to external consumers instead of Stepbit
      - Updated docs/json-request-contract-verification.md to use external consumer terminology
      - Updated docs/cli.md examples to use outputs/external_demo instead of outputs/stepbit
      - Added new canonical test file: test/test_external_consumer_compat.py
    compatibility_aliases:
      - Kept test/test_stepbit_external_provider_compat.py unchanged for historical compatibility
      - Kept stepbit-io-v1.md and stepbit-local-invocation-contract.md in place (for later archival in slice 5)
    deprecated_identifiers:
      - No public identifiers deprecated yet; old stepbit-specific docs remain for compatibility (deferred to slice 5)

  5:
    title: "docs: archive obsolete Stepbit integration material"
    type: docs_only

  final:
    title: "audit: verify de-stepbit migration completion"
    type: audit
```

## Current Decision

```yaml
decision:
  stepbit_active_architecture: false
  stepbit_active_roadmap: false
  stepbit_runtime_references:
    desktop: removed
    research_ui: removed
  stepbit_contract_references:
    status: generalized
  stepbit_visible_surfaces:
    desktop: removed
    research_ui: removed
```
