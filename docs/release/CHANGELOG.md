---
title: "DevPilot Local — Changelog"
doc_id: "DEVPL-RELEASE-CHANGELOG"
version: "0.1.0"
updated: "2026-06-25"
status: "approved"
approval: "internal"
owner: "Ordóñez"
---


## [post-h-006-a] - 2026-06-25

### Added

- `src/devpilot_core/cli_registry/` package for static CLI command registry modeling and reporting.
- `CommandDescriptor`, `CommandGroupDescriptor`, `CommandRiskLevel` and `CommandSideEffect`.
- AST-based read-only extractor over `src/devpilot_core/cli.py`.
- CLI command `python -m devpilot_core cli-registry report --json`.
- Schema `docs/schemas/cli_command_registry.schema.json` registered as `CliCommandRegistry`.
- Optional raw reports `outputs/reports/cli_command_registry.json` and `.md` when `--write-report` is used.
- Test Contract Registry v1/v2 contract `post-h-006-cli-command-registry`.

### Security

- The registry is read-only and advisory. It does not execute registered commands, import `build_parser()`, migrate handlers, rename public commands or enable dynamic handler loading.
- No network, external APIs, remote execution, connector write, plugin execution or source mutation is enabled.

### Notes

- `POST-H-006` is now approved and in progress. `POST-H-006-A` is implemented-initial; handler migration remains future `POST-H-006-B/C` scope.

## [post-h-005-e] - 2026-06-25

### Added

- `ArchitectureMapReportBuilder` for final executable ArchitectureMap report generation.
- CLI command `python -m devpilot_core architecture map --json`.
- Raw schema-valid reports `outputs/reports/architecture_map.json` and `outputs/reports/architecture_map.md` when `--write-report` is used.
- Ownership validation for missing owners and critical packages without test contracts.
- Quality-gate subgate `architecture-map` in hardening/industrial profiles.
- Formal Test Contract Registry v1/v2 contract `post-h-005-architecture-map`.
- Closure report `docs/audits/post_h_005_closure_report.md` and manifest `docs/post_h_005_e_manifest.json`.

### Security

- The final architecture map remains local-first, dry-run and advisory.
- No refactor, source mutation, runtime boundary change, tests-from-map execution, network, external APIs, remote execution, connector write or plugin execution is enabled.
- POST-H-005 closes as `implemented-initial`, not as full enterprise or production-ready architecture governance.

### Notes

- Project state advances to `last_completed_sprint=POST-H-005` and `next_sprint=POST-H-006`.
- Findings for ownership gaps and forbidden/restricted dependencies remain inputs for POST-H-006 and POST-H-007.


## [post-h-005-d] - 2026-06-25

### Added

- `ArchitectureHotspotsBuilder` for read-only architecture hotspot ranking.
- CLI command `python -m devpilot_core architecture hotspots --json`.
- Advisory score based on LOC, fan-in, fan-out, functions, CLI commands, criticality and boundary policy signals.
- Top 20 package/module hotspots with `technical_hotspot` vs `core_domain_hotspot` metadata.
- Hotspot-specific reasons and recommendations for POST-H-006/007 planning.
- POST-H-005-D audit, manifest and tests.

### Security

- Hotspot analysis reuses AST inventory and dependency graph evidence only; it does not import project modules dynamically.
- Hotspots are advisory prioritization findings only; no quality-gate enforcement, refactor or source mutation is enabled.
- No tests, subprocesses, network, external APIs, source mutations, remote execution, connector write or plugin execution are enabled.

### Notes

- This is `implemented-initial / advisory hotspot ranking`; final architecture map report, ownership validation and quality-gate integration remain future POST-H-005-E scope.


## [post-h-005-c] - 2026-06-25

### Added

- `ArchitectureDependenciesBuilder` for read-only package dependency graph generation from Python AST imports.
- CLI command `python -m devpilot_core architecture dependencies --json`.
- `DependencyEdge` materialization, package `direct_dependencies`, `fan_in` and `fan_out`.
- Advisory boundary classification for allow/restricted/forbidden/unknown dependencies.
- Sensitive dependency marking for remote/plugins/connectors.
- POST-H-005-C audit, manifest and tests.

### Security

- Dependency graph generation uses Python standard-library `ast` only and does not import project modules dynamically.
- Boundary findings are advisory warnings only; no aggressive blocking or runtime enforcement is enabled.
- No tests, subprocesses, network, external APIs, source mutations, remote execution, connector write or plugin execution are enabled.

### Notes

- This is `implemented-initial / advisory dependency graph`; hotspot scoring, final architecture report and quality-gate integration remain future POST-H-005 micro-sprints.



## [post-h-005-b] - 2026-06-25

### Added

- `ArchitectureInventoryBuilder` for read-only AST inventory of `src/devpilot_core`.
- CLI command `python -m devpilot_core architecture inventory --json`.
- Module/package evidence for LOC, classes, functions, imports, approximate exports, CLI commands, CLI handlers and heuristic test mapping.
- POST-H-005-B audit, manifest and tests.

### Security

- Inventory uses Python standard-library `ast` only and does not import project modules dynamically.
- No tests, subprocesses, network, external APIs, source mutations, remote execution, connector write or plugin execution are enabled.

### Notes

- This is `implemented-initial / AST inventory only`; dependency graph, fan-in/fan-out, hotspots, final report and quality-gate integration remain future POST-H-005 micro-sprints.

## [post-h-005-a] - 2026-06-24

### Added

- `ArchitectureMap` schema registered as `SCHEMA-DEVPL-ARCHITECTURE-MAP-V1`.
- Architecture model package with `ArchitectureMap`, `ArchitectureModule`, `ArchitecturePackage`, `DependencyEdge`, `Hotspot` and `OwnershipEntry`.
- Initial `.devpilot/architecture/ownership_registry.json` covering CLI, policy, schemas, agents, testing, quality and industrial packages.
- POST-H-005-A audit, manifest, fixtures and tests.

### Notes

- This is `implemented-initial / schema-only`; AST inventory, dependency graph, hotspots, report builder and quality-gate integration remain future POST-H-005 micro-sprints.
- No network, external APIs, source mutations, remote execution, connector write or plugin execution were enabled.

## [post-h-004-e] - 2026-06-24

### Added

- Subgate `miasi-semantic-validate` inside `quality-gate hardening` and `industrial` profiles.
- Formal Test Contract Registry v1/v2 contract `post-h-004-miasi-semantic-validator`.
- Closure report `docs/audits/post_h_004_closure_report.md` and manifest `docs/post_h_004_e_manifest.json`.
- Documentation sync for README, runbook and Policy/MIASI security documentation.

### Security

- The semantic validator remains local-first, dry-run and non-executing.
- The quality gate does not execute agents, tools, evals, pytest from JSON, network calls, external APIs, connectors, plugins or remote runners.
- POST-H-004 closes as `implemented-initial`, not as full production-ready-local.

### Notes

- Project state advances to `last_completed_sprint=POST-H-004` and `next_sprint=POST-H-005`.
- The remaining high-risk controlled-write warnings stay visible for future Approval/RBAC hardening.

## [post-h-004-d] - 2026-06-24

### Added

- Reglas semánticas `SEM-OBSERVABILITY-001`, `SEM-EVAL-COVERAGE-001` y `SEM-TEST-CONTRACT-COVERAGE-001` dentro de `miasi semantic-validate`.
- Cruce declarativo de agentes A3+/high-risk con `observability_required` y `eval_required`.
- Validación de handoff traces para capacidades multiagent/workflow.
- Validación de fixtures/evals locales red-team, advanced-agentic, plugin-ecosystem, identity-rbac y remote-enterprise.
- Cruce preliminar con Test Contract Registry v1/v2 y warning controlado por ausencia de contrato formal del semantic validator.
- Reporte `docs/audits/post_h_004_d_observability_evals_test_contracts_report.md` y manifest `docs/post_h_004_d_manifest.json`.

### Security

- No se ejecutan agentes, tools, evals, pytest desde JSON, red, APIs externas, conectores, plugins ni remote runners.
- Fixtures/evals se validan como evidencia local determinista; cualquier red/API externa/LLM judge declarado bloquea.
- La integración como subgate de quality-gate se reserva para `POST-H-004-E`.

### Notes

- Capacidad `implemented-initial`; conserva warnings por deuda de approval/RBAC en `controlled_write` high-risk y por contrato TCR formal pendiente.


# Changelog

## [post-h-004-c] - 2026-06-24

### Added

- Approval/RBAC/security guard rules inside `MiasiSemanticValidator`.
- Semantic checks for concrete approval metadata, generic approval blocking, Identity Registry defaults, active actor/roles, RBAC approval permissions, network/cost guard semantics and remote/plugin/connector write/execute no-go guards.
- New unsafe fixtures: missing identity/RBAC, generic approval, network cost without CostGuard, and connector write without ADR/sandbox guard.

### Security

- The validator remains read-only, local-first and non-executing.
- `semantic-validate` still does not execute agents, tools, pytest, subprocesses, connectors, plugins, remote runners, network calls or external APIs.
- Existing high-risk `controlled_write` implemented-initial paths remain warnings until explicit approval/RBAC policy is formalized.


## [post-h-004-b] - 2026-06-24

### Added

- `MiasiSemanticValidator` for local, non-executing agent/tool/policy semantic validation.
- CLI `python -m devpilot_core miasi semantic-validate --json`.
- Fixtures under `tests/fixtures/miasi/` for valid bundle, unknown tools, missing approval, policy contradictions and plugin execution no-go.
- Tests `tests/test_miasi_semantic_validator.py` and `tests/test_miasi_semantic_validator_fixtures.py`.
- Manifest `docs/post_h_004_b_manifest.json` and audit report `docs/audits/post_h_004_b_agent_tool_policy_rules_report.md`.

### Security

- The validator does not execute agents, tools, pytest, subprocesses, connectors, plugins, remote runners, network calls or external APIs.
- remote/plugin/connector execute no-go rules remain blocking when declared as `allow`.
- Current high-risk `controlled_write` local/sandbox/registry flows without explicit approval are emitted as warnings for POST-H-004-C hardening, not accepted as production-ready behavior.



## [post-h-004-a] - 2026-06-24

### Added

- `MiasiSemanticReport`, `SemanticFinding` and `SemanticRuleResult` as the semantic report model for `POST-H-004`.
- `docs/schemas/miasi_semantic_report.schema.json` and schema catalog entry `SCHEMA-DEVPL-MIASI-SEMANTIC-REPORT-V1`.
- Severity mapping `info/warning/error/block` for future semantic rules.
- Fixtures and tests for valid and invalid semantic report payloads.

### Security

- The report contract requires `dry_run=true`, `network_used=false`, `external_api_used=false`, `mutations_performed=false` and `source_mutations_performed=false`.
- No semantic rules, agent execution, tool execution, remote execution, connector write or plugin execution are enabled in this micro-sprint.

## [post-h-003-e] - 2026-06-24

- Closes `POST-H-003 — Test Contract Registry 2.0` as `implemented-initial`.
- Adds `test-contract-registry-v2` as a local non-executing subgate in `quality-gate run --profile hardening`.
- Adds `post-h-003-test-contract-registry-2` to the v1 Test Contract Registry and regenerates the v2 registry with 88 contracts.
- Updates project state to `last_completed_sprint=POST-H-003` and `next_sprint=POST-H-004`.
- Synchronizes README, runbook, backlog, ADR-POSTH-002, manifest and closure report.


All notable changes to DevPilot Local are documented in this file.

This changelog follows a Keep a Changelog-compatible category structure and is generated from local sprint manifests.


## [post-h-003-d] - 2026-06-24

### Added

- `TestImpactAnalyzerV2` in `src/devpilot_core/testing/impact_v2.py`.
- CLI `python -m devpilot_core test-impact analyze-v2 --changed-paths <path> --json`.
- Impact matching against v2 `test_files`, `watched_paths` and `validates`.
- Explicit heuristics for policy/security, schemas, CLI/API, agentic runtime and release changes.
- Tests `tests/test_test_impact_v2.py`.
- Manifest `docs/post_h_003_d_manifest.json` and audit `docs/audits/post_h_003_d_test_impact_v2_report.md`.

### Changed

- `docs/backlogs/POST-H-003_test_contract_registry_2.md` moves to version `0.5.0` and records `POST-H-003-D` as `implemented-initial`.
- `docs/04_quality/test_contract_registry_2_design.md` documents impact analyzer v2 semantics.
- README and runbook now point to `POST-H-003-E` as next micro-sprint.

### Security

- `analyze-v2` does not execute pytest or subprocesses.
- The command is local-only, dry-run, no network, no external APIs and no source mutations.
- Recommendations are operator-facing plans, not automatic execution.


## [post-h-003-c] - 2026-06-24

### Added

- `TestContractRegistryV2Validator` in `src/devpilot_core/testing/profiles_v2.py`.
- CLI `python -m devpilot_core test-contracts validate-v2 --json`.
- CLI `python -m devpilot_core test-contracts profile --profile <id> --json`.
- Profiles `p0-critical`, `security`, `release`, `impact` and `docs-historical` as read-only selectors.
- Tests `tests/test_test_contract_registry_profiles_v2.py`.
- Manifest `docs/post_h_003_c_manifest.json` and audit `docs/audits/post_h_003_c_test_contract_registry_v2_validator_report.md`.

### Changed

- `docs/backlogs/POST-H-003_test_contract_registry_2.md` moves to version `0.4.0` and records `POST-H-003-C` as `implemented-initial`.
- `docs/04_quality/test_contract_registry_2_design.md` documents validator and profile semantics.
- README and runbook now point to `POST-H-003-D` as next micro-sprint.

### Security

- Profiles select contracts and recommended commands only; they do not execute pytest or subprocesses.
- Recommended commands are inspected against a local allowlist.
- No network, external API, remote execution, connector write or plugin execution is enabled.

## [post-h-003-b] - 2026-06-24

### Added

- `TestContractRegistryV2Migrator` in `src/devpilot_core/testing/migration.py` for deterministic v1 → v2 dry-run migration.
- CLI `python -m devpilot_core test-contracts migrate-v2 --dry-run --json`.
- Explicit output generation through `--write-output .devpilot/testing/test_contract_registry_v2.json`.
- Migrated registry `.devpilot/testing/test_contract_registry_v2.json` with 87 v2 contracts.
- Tests `tests/test_test_contract_registry_migration.py`.
- Manifest `docs/post_h_003_b_manifest.json` and audit `docs/audits/post_h_003_b_test_contract_registry_v2_migration_report.md`.

### Changed

- `docs/backlogs/POST-H-003_test_contract_registry_2.md` moves to version `0.3.0` and records `POST-H-003-B` as `implemented-initial`.
- `docs/04_quality/test_contract_registry_2_design.md` documents migration semantics and compatibility.
- `docs/schemas/test_contract_registry_v2.schema.json` accepts POST-H-003-B generated payloads while preserving POST-H-003-A fixtures.
- `docs/schemas/schema_catalog.json` moves to version `1.3.0` and updates the v2 schema entry metadata.
- README and runbook now point to `POST-H-003-C` as next micro-sprint.

### Security

- The migrator refuses to overwrite `.devpilot/testing/test_contract_registry.json`.
- Dry-run is the default mode.
- No tests are executed from JSON.
- No network, external API, remote execution, connector write or plugin execution is enabled.

### Notes

- Classifications are deterministic but initial; `TEST_CONTRACT_V2_CLASSIFICATION_GAP` findings are expected and must be refined by `POST-H-003-C/D/E`.

## [post-h-003-a] - 2026-06-24

### Added

- Schema `docs/schemas/test_contract_registry_v2.schema.json` registrado como `SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V2` / `TestContractRegistryV2`.
- Helper `TestContractRegistryV2Design` para validar fixtures o payloads v2 sin ejecutar pruebas ni migrar v1.
- Fixtures válidos e inválidos en `tests/fixtures/test_contract_registry_v2/`.
- Pruebas focales `tests/test_test_contract_registry_v2.py`.
- Documento `docs/04_quality/test_contract_registry_2_design.md`, audit `docs/audits/post_h_003_a_test_contract_registry_v2_schema_report.md` y manifest `docs/post_h_003_a_manifest.json`.

### Changed

- `docs/backlogs/POST-H-003_test_contract_registry_2.md` pasa a `status: approved` y versión `0.2.0`.
- `docs/schemas/schema_catalog.json` pasa a versión `1.2.0` e incluye el schema v2.
- README y runbook quedan sincronizados con `POST-H-003-A` y siguiente micro-sprint `POST-H-003-B`.

### Security

- No se reemplaza el registry v1.
- No se habilita red, APIs externas, remote execution, connector write, plugin execution ni ejecución automática de tests desde JSON.
- El schema exige flags explícitos para network, external API y mutaciones; cualquier excepción requiere `safety_exception` y aprobación humana.

### Notes

- Esta entrega es `implemented-initial`; la migración v1 → v2 queda para `POST-H-003-B` y el CLI `validate-v2` para `POST-H-003-C`.




## [post-h-002-c] - 2026-06-24

### Added

- `MaturityDashboardBuilder` in `src/devpilot_core/maturity/dashboard.py` to build schema-backed maturity dashboards from POST-H source bundles.
- `DashboardBuildResult` and `render_maturity_dashboard_markdown()` for in-memory JSON/Markdown generation.
- No-go blocked capabilities for remote execution, connector write and plugin execution based on `SEC-001`, `SEC-002` and `SEC-003`.
- `docs/post_h_002_c_manifest.json` and `docs/audits/post_h_002_c_dashboard_builder_report.md`.

### Changed

- `README.md`, `docs/05_operations/runbook.md` and `docs/backlogs/POST-H-002_maturity_dashboard_local.md` now mark `POST-H-002-C` as `implemented-initial` and `POST-H-002-D` as next.

### Safety

- No CLI command is added in this micro-sprint.
- No reports are written to `outputs/reports` yet.
- No remote execution, connector write, plugin execution, external APIs, network or runtime mutation is enabled.

## [post-h-002-b] - 2026-06-24

### Added

- `POST-H-002-B — Lectores de fuentes post-H` como capa read-only de extracción de evidencia para el dashboard local de madurez.
- Módulo `src/devpilot_core/maturity/sources.py` con `PostHSourceReader`, `SourceSpec`, `SourceReadResult` y `PostHSourceBundle`.
- Lectura determinística de manifest, decision matrix, risk register, test/cost assessment, roadmap JSON y Test Contract Registry.
- Fallback controlado para documentos Markdown canónicos de `POST-H-EVAL-001`.
- Manifest y reporte de auditoría del micro-sprint.

### Changed

- `docs/backlogs/POST-H-002_maturity_dashboard_local.md` documenta `POST-H-002-B` como `implemented-initial` y deja `POST-H-002-C` como siguiente micro-sprint.
- `README.md` y `docs/05_operations/runbook.md` quedan sincronizados con la operación de los lectores.

### Security

- Los lectores son read-only y no escriben reportes, no mutan fuentes, no llaman red, no usan APIs externas y no habilitan remote execution, connector write ni plugin execution.


## [post-h-002-a] - 2026-06-23

### Added

- `POST-H-002-A — Modelo de madurez y schema` como primera base del dashboard local de madurez.
- Paquete `src/devpilot_core/maturity/` con modelos `MaturityDashboard`, `MaturityCapability`, `RoadmapDependency` y `SafetySignal`.
- Schema `docs/schemas/maturity_dashboard.schema.json` y registro `SCHEMA-DEVPL-MATURITY-DASHBOARD-V1` en `docs/schemas/schema_catalog.json`.
- Pruebas focales `tests/test_post_h_002_maturity_dashboard.py`.

### Changed

- `docs/backlogs/POST-H-002_maturity_dashboard_local.md` pasa a `status: approved` y documenta el avance `POST-H-002-A` como `implemented-initial`.

### Security

- El nuevo modelo no habilita remote execution, connector write, plugin execution ni APIs externas.
- El schema permite `production-ready-local`, pero bloquea el claim genérico `production-ready`; la declaración final queda reservada para `POST-H-025`.


## [post-h-eval-001] - 2026-06-23

### Added

- `POST-H-EVAL-001` — Evaluación integral del baseline DevPilot post-Fase H.
- Se agregaron assessment baseline, matriz de madurez, mapa arquitectónico, risk register, evaluación de testing/costos/contratos, roadmap priorizado, ADRs post-H y closure report.
- Se agregó `tests/test_post_h_eval_001_documentation.py` como prueba documental global del hito.

### Changed

- `docs/post_h_eval_001_manifest.json` queda en `status=closed` y habilita `POST-H-002 — Maturity dashboard local basado en assessment post-H` como siguiente hito.
- El Test Contract Registry v1 incorpora el contrato documental global `post-h-eval-001-documentation` sin modificar el contrato único de estado global mutable.

### Security

- No se habilitó remote execution, connector write, plugin execution ni APIs externas.
- El cierre conserva el enfoque local-first, dry-run y sin sobredeclarar madurez enterprise ni compliance certificada.

## [post-H-001] - 2026-06-19

### Added

- `POST-H-001` — Industrial hardening de tests y contratos. Se agregó `.devpilot/testing/test_contract_registry.json`, `.devpilot/project_state.json`, `test-contracts validate`, `project-state validate`, `test-impact analyze` y `quality-gate run --profile hardening`.
- Se agregaron schemas `SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V1`, `SCHEMA-DEVPL-PROJECT-STATE-V1` y `SCHEMA-DEVPL-POST-H-MANIFEST-V1`.

### Changed

- Los tests documentales históricos de Fase H dejan de duplicar estado global mutable; esa responsabilidad queda centralizada en `tests/test_project_global_state.py`.

### Security

- El analizador de impacto es conservador: ante rutas desconocidas o cambios core recomienda `pytest -q`. No ejecuta comandos arbitrarios ni red.

## [0.1.0] - 2026-06-19

Release ID: `DEVPL-0.1.0`  
Range: `FUNC-SPRINT-74` → `FUNC-SPRINT-99`  
Source: `docs/functional_sprint_*_manifest.json`

### Added

- `FUNC-SPRINT-74` — Se incorporó `ADR de release, versionado y productización`. Source: `docs/functional_sprint_74_manifest.json`; audit: `docs/audits/func_sprint_74_release_versioning_audit.md`. Artefactos: `docs/02_architecture/adrs/ADR-0014-release-versioning-packaging.md`, `docs/05_operations/release_policy.md`, `docs/05_operations/release_artifacts_matrix.md`, `docs/audits/func_sprint_74_release_versioning_audit.md` y 2 artefactos adicionales.
- `FUNC-SPRINT-75` — Se incorporó `Quality Gate local unificado`. Source: `docs/functional_sprint_75_manifest.json`; audit: `docs/audits/func_sprint_75_quality_gate_audit.md`. Artefactos: `src/devpilot_core/quality/__init__.py`, `src/devpilot_core/quality/gate.py`, `tests/test_quality_gate.py`, `tests/test_sprint_75_documentation.py` y 2 artefactos adicionales.
- `FUNC-SPRINT-76` — Se incorporó `CI local y workflow scaffolding`. Source: `docs/functional_sprint_76_manifest.json`; audit: `docs/audits/func_sprint_76_ci_scaffolding_audit.md`. Artefactos: `.github/workflows/devpilot-ci.yml`, `docs/05_operations/ci_cd_local.md`, `docs/audits/func_sprint_76_ci_scaffolding_audit.md`, `docs/functional_sprint_76_manifest.json` y 2 artefactos adicionales.
- `FUNC-SPRINT-77` — Se incorporó `Release metadata y Release Manifest`. Source: `docs/functional_sprint_77_manifest.json`; audit: `docs/audits/func_sprint_77_release_manifest_audit.md`. Artefactos: `src/devpilot_core/release/__init__.py`, `src/devpilot_core/release/manifest.py`, `docs/05_operations/release_manifest.md`, `docs/audits/func_sprint_77_release_manifest_audit.md` y 3 artefactos adicionales.
- `FUNC-SPRINT-78` — Se incorporó `Changelog generator y política de cambios`. Source: `docs/functional_sprint_78_manifest.json`; audit: `docs/audits/func_sprint_78_changelog_audit.md`. Artefactos: `src/devpilot_core/release/changelog.py`, `docs/05_operations/change_policy.md`, `docs/release/CHANGELOG.md`, `docs/audits/func_sprint_78_changelog_audit.md` y 3 artefactos adicionales.
- `FUNC-SPRINT-79` — Se incorporó `Packaging Python y ZIP limpio reproducible`. Source: `docs/functional_sprint_79_manifest.json`; audit: `docs/audits/func_sprint_79_packaging_audit.md`. Artefactos: `src/devpilot_core/release/package_builder.py`, `docs/05_operations/packaging.md`, `docs/audits/func_sprint_79_packaging_audit.md`, `docs/functional_sprint_79_manifest.json` y 2 artefactos adicionales.
- `FUNC-SPRINT-80` — Se incorporó `SBOM y supply-chain baseline`. Source: `docs/functional_sprint_80_manifest.json`; audit: `docs/audits/func_sprint_80_sbom_supply_chain_audit.md`. Artefactos: `src/devpilot_core/release/sbom.py`, `docs/03_security/supply_chain_policy.md`, `docs/audits/func_sprint_80_sbom_supply_chain_audit.md`, `docs/functional_sprint_80_manifest.json` y 2 artefactos adicionales.
- `FUNC-SPRINT-81` — Se incorporó `Checksums, smoke tests y verificación de release`. Source: `docs/functional_sprint_81_manifest.json`; audit: `docs/audits/func_sprint_81_release_verification_audit.md`. Artefactos: `src/devpilot_core/release/verification.py`, `docs/05_operations/release_verification.md`, `docs/audits/func_sprint_81_release_verification_audit.md`, `docs/functional_sprint_81_manifest.json` y 2 artefactos adicionales.
- `FUNC-SPRINT-82` — Se incorporó `Estrategia de instalación e installer preliminar`. Source: `docs/functional_sprint_82_manifest.json`. Artefactos: `src/devpilot_core/release/installation.py`, `docs/05_operations/install_guide.md`, `docs/02_architecture/adrs/ADR-0015-installation-strategy.md`, `docs/audits/func_sprint_82_installation_audit.md` y 3 artefactos adicionales.
- `FUNC-SPRINT-83` — Se incorporó `Backup, restore y upgrade local`. Source: `docs/functional_sprint_83_manifest.json`. Artefactos: `src/devpilot_core/release/backup.py`, `src/devpilot_core/release/upgrade.py`, `docs/05_operations/backup_restore_upgrade.md`, `docs/audits/func_sprint_83_backup_upgrade_audit.md` y 3 artefactos adicionales.
- `FUNC-SPRINT-84` — Se incorporó `ReleaseAgent MVP dry-run y cierre Fase G`. Source: `docs/functional_sprint_84_manifest.json`. Artefactos: `src/devpilot_core/agents/release_agent.py`, `docs/audits/phase_g_productization_release_closure.md`, `docs/audits/func_sprint_84_release_agent_audit.md`, `docs/functional_sprint_84_manifest.json` y 2 artefactos adicionales.
- `FUNC-SPRINT-85` — Se incorporó `ADR de arquitectura avanzada agentic/enterprise`. Source: `docs/functional_sprint_85_manifest.json`. Artefactos: `docs/02_architecture/adrs/ADR-0016-advanced-agentic-enterprise.md`, `docs/03_security/advanced_agentic_threat_model.md`, `docs/audits/func_sprint_85_advanced_architecture_audit.md`, `docs/functional_sprint_85_manifest.json` y 1 artefactos adicionales.
- `FUNC-SPRINT-86` — Se incorporó `Agent session state y memoria operativa controlada`. Source: `docs/functional_sprint_86_manifest.json`. Artefactos: `src/devpilot_core/agents/session.py`, `docs/06_miasi/agent_session_card.md`, `docs/audits/func_sprint_86_agent_session_audit.md`, `docs/functional_sprint_86_manifest.json` y 2 artefactos adicionales.
- `FUNC-SPRINT-87` — Se incorporó `RAG documental local MVP`. Source: `docs/functional_sprint_87_manifest.json`. Artefactos: `src/devpilot_core/rag/__init__.py`, `src/devpilot_core/rag/indexer.py`, `src/devpilot_core/rag/retriever.py`, `docs/06_miasi/rag_card.md` y 4 artefactos adicionales.
- `FUNC-SPRINT-88` — Se incorporó `MCP threat model y Connector Registry`. Source: `docs/functional_sprint_88_manifest.json`. Artefactos: `src/devpilot_core/connectors/__init__.py`, `src/devpilot_core/connectors/registry.py`, `.devpilot/connectors/connector_registry.json`, `docs/schemas/connector_registry.schema.json` y 6 artefactos adicionales.
- `FUNC-SPRINT-89` — Se incorporó `MCP MVP controlado y herramientas read-only`. Source: `docs/functional_sprint_89_manifest.json`. Artefactos: `src/devpilot_core/connectors/adapter.py`, `tests/test_connector_adapter.py`, `tests/test_sprint_89_documentation.py`, `docs/audits/func_sprint_89_mcp_mvp_audit.md` y 1 artefactos adicionales.
- `FUNC-SPRINT-90` — Se incorporó `MultiAgentCoordinator MVP y handoffs gobernados`. Source: `docs/functional_sprint_90_manifest.json`. Artefactos: `src/devpilot_core/multiagent/__init__.py`, `src/devpilot_core/multiagent/coordinator.py`, `src/devpilot_core/multiagent/handoff.py`, `tests/test_multiagent_coordinator.py` y 3 artefactos adicionales.
- `FUNC-SPRINT-91` — Se incorporó `Workflows multiagente SDLC dry-run`. Source: `docs/functional_sprint_91_manifest.json`. Artefactos: `.devpilot/workflows/sdlc_review.json`, `docs/schemas/multiagent_workflow.schema.json`, `src/devpilot_core/multiagent/workflow.py`, `evals/fixtures/multiagent_workflow_sdlc_review_cases.json` y 4 artefactos adicionales.
- `FUNC-SPRINT-92` — Se incorporó `Evaluación avanzada, red teaming y safety scoring`. Source: `docs/functional_sprint_92_manifest.json`; audit: `docs/audits/func_sprint_92_advanced_evals_audit.md`. Artefactos: `evals/fixtures/advanced_agentic_eval_cases.json`, `evals/fixtures/red_team_agentic_eval_cases.json`, `src/devpilot_core/evals/safety.py`, `tests/test_advanced_evals.py` y 3 artefactos adicionales.
- `FUNC-SPRINT-93` — Se incorporó `Plugin y connector ecosystem controlado`. Source: `docs/functional_sprint_93_manifest.json`; audit: `docs/audits/func_sprint_93_plugin_ecosystem_audit.md`. Artefactos: `src/devpilot_core/plugins/__init__.py`, `src/devpilot_core/plugins/registry.py`, `.devpilot/plugins/plugin_registry.json`, `docs/schemas/plugin_manifest.schema.json` y 5 artefactos adicionales.
- `FUNC-SPRINT-94` — Se incorporó `Multiworkspace Manager y portfolio local`. Source: `docs/functional_sprint_94_manifest.json`. Artefactos: `src/devpilot_core/workspace/registry.py`, `src/devpilot_core/portfolio/__init__.py`, `src/devpilot_core/portfolio/status.py`, `.devpilot/workspaces/workspace_registry.json` y 6 artefactos adicionales.
- `FUNC-SPRINT-95` — Se incorporó `RBAC local y modelo de identidad`. Source: `docs/functional_sprint_95_manifest.json`. Artefactos: `src/devpilot_core/identity/__init__.py`, `src/devpilot_core/identity/models.py`, `src/devpilot_core/identity/rbac.py`, `.devpilot/identity/identity_registry.json` y 6 artefactos adicionales.
- `FUNC-SPRINT-96` — Se incorporó `Colaboración local y audit packs`. Source: `docs/functional_sprint_96_manifest.json`. Artefactos: `src/devpilot_core/auditpack/__init__.py`, `src/devpilot_core/auditpack/builder.py`, `docs/schemas/audit_pack_manifest.schema.json`, `evals/fixtures/audit_pack_integrity_eval_cases.json` y 5 artefactos adicionales.
- `FUNC-SPRINT-97` — Se incorporó `Compliance packs y policy packs`. Source: `docs/functional_sprint_97_manifest.json`. Artefactos: `src/devpilot_core/compliance/__init__.py`, `src/devpilot_core/compliance/registry.py`, `src/devpilot_core/compliance/runner.py`, `.devpilot/compliance/packs.json` y 6 artefactos adicionales.

### Changed

- `FUNC-SPRINT-74` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_74_manifest.json`; audit: `docs/audits/func_sprint_74_release_versioning_audit.md`. Artefactos: `README.md`, `docs/05_operations/runbook.md`, `docs/devpilot_backlog_fase_G_productizacion_release.md`, `docs/functional_backlog_after_precode.md` y 1 artefactos adicionales.
- `FUNC-SPRINT-75` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_75_manifest.json`; audit: `docs/audits/func_sprint_75_quality_gate_audit.md`. Artefactos: `src/devpilot_core/cli.py`, `README.md`, `docs/05_operations/runbook.md`, `docs/devpilot_backlog_fase_G_productizacion_release.md` y 2 artefactos adicionales.
- `FUNC-SPRINT-76` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_76_manifest.json`; audit: `docs/audits/func_sprint_76_ci_scaffolding_audit.md`. Artefactos: `src/devpilot_core/quality/gate.py`, `src/devpilot_core/cli.py`, `README.md`, `docs/05_operations/runbook.md` y 4 artefactos adicionales.
- `FUNC-SPRINT-77` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_77_manifest.json`; audit: `docs/audits/func_sprint_77_release_manifest_audit.md`. Artefactos: `src/devpilot_core/cli.py`, `README.md`, `docs/05_operations/runbook.md`, `docs/devpilot_backlog_fase_G_productizacion_release.md` y 2 artefactos adicionales.
- `FUNC-SPRINT-78` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_78_manifest.json`; audit: `docs/audits/func_sprint_78_changelog_audit.md`. Artefactos: `src/devpilot_core/cli.py`, `src/devpilot_core/release/__init__.py`, `src/devpilot_core/release/manifest.py`, `README.md` y 5 artefactos adicionales.
- `FUNC-SPRINT-79` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_79_manifest.json`; audit: `docs/audits/func_sprint_79_packaging_audit.md`. Artefactos: `src/devpilot_core/cli.py`, `src/devpilot_core/release/__init__.py`, `src/devpilot_core/release/manifest.py`, `README.md` y 6 artefactos adicionales.
- `FUNC-SPRINT-80` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_80_manifest.json`; audit: `docs/audits/func_sprint_80_sbom_supply_chain_audit.md`. Artefactos: `src/devpilot_core/cli.py`, `src/devpilot_core/release/__init__.py`, `src/devpilot_core/release/manifest.py`, `README.md` y 8 artefactos adicionales.
- `FUNC-SPRINT-81` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_81_manifest.json`; audit: `docs/audits/func_sprint_81_release_verification_audit.md`. Artefactos: `src/devpilot_core/cli.py`, `src/devpilot_core/release/__init__.py`, `src/devpilot_core/release/manifest.py`, `README.md` y 7 artefactos adicionales.
- `FUNC-SPRINT-82` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_82_manifest.json`. Artefactos: `src/devpilot_core/cli.py`, `src/devpilot_core/release/__init__.py`, `src/devpilot_core/release/manifest.py`, `README.md` y 7 artefactos adicionales.
- `FUNC-SPRINT-83` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_83_manifest.json`. Artefactos: `src/devpilot_core/cli.py`, `src/devpilot_core/release/__init__.py`, `src/devpilot_core/release/manifest.py`, `README.md` y 7 artefactos adicionales.
- `FUNC-SPRINT-84` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_84_manifest.json`. Artefactos: `src/devpilot_core/agents/__init__.py`, `src/devpilot_core/agents/runtime.py`, `src/devpilot_core/cli.py`, `src/devpilot_core/quality/gate.py` y 14 artefactos adicionales.
- `FUNC-SPRINT-85` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_85_manifest.json`. Artefactos: `README.md`, `docs/05_operations/runbook.md`, `docs/devpilot_backlog_fase_H_capacidades_avanzadas.md`, `docs/functional_backlog_after_precode.md` y 11 artefactos adicionales.
- `FUNC-SPRINT-86` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_86_manifest.json`. Artefactos: `src/devpilot_core/agents/__init__.py`, `src/devpilot_core/agents/runtime.py`, `src/devpilot_core/cli.py`, `src/devpilot_core/release/package_builder.py` y 9 artefactos adicionales.
- `FUNC-SPRINT-87` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_87_manifest.json`. Artefactos: `src/devpilot_core/cli.py`, `src/devpilot_core/release/package_builder.py`, `src/devpilot_core/release/verification.py`, `.devpilot/miasi/tool_registry.json` y 7 artefactos adicionales.
- `FUNC-SPRINT-88` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_88_manifest.json`. Artefactos: `src/devpilot_core/cli.py`, `.devpilot/miasi/tool_registry.json`, `.devpilot/miasi/policy_matrix.json`, `docs/schemas/schema_catalog.json` y 7 artefactos adicionales.
- `FUNC-SPRINT-89` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_89_manifest.json`. Artefactos: `src/devpilot_core/connectors/__init__.py`, `src/devpilot_core/cli.py`, `.devpilot/connectors/connector_registry.json`, `.devpilot/miasi/tool_registry.json` y 10 artefactos adicionales.
- `FUNC-SPRINT-90` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_90_manifest.json`. Artefactos: `src/devpilot_core/cli.py`, `.devpilot/miasi/agent_registry.json`, `.devpilot/miasi/tool_registry.json`, `.devpilot/miasi/policy_matrix.json` y 13 artefactos adicionales.
- `FUNC-SPRINT-91` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_91_manifest.json`. Artefactos: `README.md`, `docs/05_operations/runbook.md`, `docs/devpilot_backlog_fase_H_capacidades_avanzadas.md`, `docs/functional_backlog_after_precode.md` y 8 artefactos adicionales.
- `FUNC-SPRINT-92` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_92_manifest.json`; audit: `docs/audits/func_sprint_92_advanced_evals_audit.md`. Artefactos: `src/devpilot_core/evals/__init__.py`, `src/devpilot_core/evals/runner.py`, `src/devpilot_core/quality/gate.py`, `.devpilot/miasi/agent_registry.json` y 16 artefactos adicionales.
- `FUNC-SPRINT-93` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_93_manifest.json`; audit: `docs/audits/func_sprint_93_plugin_ecosystem_audit.md`. Artefactos: `src/devpilot_core/cli.py`, `src/devpilot_core/evals/safety.py`, `src/devpilot_core/evals/runner.py`, `src/devpilot_core/quality/gate.py` y 12 artefactos adicionales.
- `FUNC-SPRINT-94` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_94_manifest.json`. Artefactos: `src/devpilot_core/workspace/__init__.py`, `src/devpilot_core/cli.py`, `src/devpilot_core/evals/safety.py`, `src/devpilot_core/evals/runner.py` y 10 artefactos adicionales.
- `FUNC-SPRINT-95` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_95_manifest.json`. Artefactos: `src/devpilot_core/cli.py`, `src/devpilot_core/policy/engine.py`, `src/devpilot_core/approval/service.py`, `src/devpilot_core/evals/safety.py` y 13 artefactos adicionales.
- `FUNC-SPRINT-96` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_96_manifest.json`. Artefactos: `src/devpilot_core/cli.py`, `src/devpilot_core/evals/safety.py`, `src/devpilot_core/evals/runner.py`, `src/devpilot_core/quality/gate.py` y 12 artefactos adicionales.
- `FUNC-SPRINT-97` — Se sincronizaron artefactos de ingeniería y contratos existentes. Source: `docs/functional_sprint_97_manifest.json`. Artefactos: `src/devpilot_core/cli.py`, `src/devpilot_core/evals/safety.py`, `src/devpilot_core/evals/runner.py`, `src/devpilot_core/quality/gate.py` y 10 artefactos adicionales.

### Deprecated

- No entries declared by local sprint manifests for this category.

### Removed

- No entries declared by local sprint manifests for this category.

### Fixed

- `FUNC-SPRINT-75` — Se registró una corrección soportada por el manifest funcional del sprint. Source: `docs/functional_sprint_75_manifest.json`; audit: `docs/audits/func_sprint_75_quality_gate_audit.md`. quality-gate run --json returns a parseable CommandResult.; Subgates include readiness, standards, MIASI, eval fixture readiness and app contract.; +3 criterios adicionales
- `FUNC-SPRINT-78` — Se registró una corrección soportada por el manifest funcional del sprint. Source: `docs/functional_sprint_78_manifest.json`; audit: `docs/audits/func_sprint_78_changelog_audit.md`. Changelog is human-readable and Keep a Changelog-compatible.; Changelog is generated from local manifests and includes traceability to sprint manifests.; +4 criterios adicionales
- `FUNC-SPRINT-91` — Se registró una corrección soportada por el manifest funcional del sprint. Source: `docs/functional_sprint_91_manifest.json`. Workflow sdlc-review validates against docs/schemas/multiagent_workflow.schema.json.; multiagent workflow run returns ok=true in --dry-run mode.; +3 criterios adicionales
- `FUNC-SPRINT-92` — Se registró una corrección soportada por el manifest funcional del sprint. Source: `docs/functional_sprint_92_manifest.json`; audit: `docs/audits/func_sprint_92_advanced_evals_audit.md`. advanced-agentic eval suite returns ok=true and safety_score >= 90; red-team eval suite returns ok=true and includes adversarial cases; +4 criterios adicionales
- `FUNC-SPRINT-93` — Se registró una corrección soportada por el manifest funcional del sprint. Source: `docs/functional_sprint_93_manifest.json`; audit: `docs/audits/func_sprint_93_plugin_ecosystem_audit.md`. Plugin Registry validates structurally and semantically.; Plugin loader dry-run emits trace evidence without loading arbitrary code.; +2 criterios adicionales
- `FUNC-SPRINT-94` — Se registró una corrección soportada por el manifest funcional del sprint. Source: `docs/functional_sprint_94_manifest.json`. Multiworkspace Registry valida contra schema.; workspace register/list/select funcionan en JSON.; +3 criterios adicionales
- `FUNC-SPRINT-95` — Se registró una corrección soportada por el manifest funcional del sprint. Source: `docs/functional_sprint_95_manifest.json`. Roles mínimos owner, architect, developer, reviewer, operator y agent-supervisor existen.; Identity Registry valida contra schema.; +4 criterios adicionales
- `FUNC-SPRINT-96` — Se registró una corrección soportada por el manifest funcional del sprint. Source: `docs/functional_sprint_96_manifest.json`. Audit pack build retorna ok=true y escribe ZIP bajo outputs/auditpacks.; Audit pack incluye audit-pack-manifest.json con checksums SHA-256.; +4 criterios adicionales
- `FUNC-SPRINT-97` — Se registró una corrección soportada por el manifest funcional del sprint. Source: `docs/functional_sprint_97_manifest.json`. Packs declarativos y validables por schema.; Runner usa gates existentes y PolicyEngine.; +4 criterios adicionales

### Security

- `FUNC-SPRINT-74` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_74_manifest.json`; audit: `docs/audits/func_sprint_74_release_versioning_audit.md`. Controles declarados: `destructive_actions_added=False`, `external_publication_out_of_scope=True`.
- `FUNC-SPRINT-75` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_75_manifest.json`; audit: `docs/audits/func_sprint_75_quality_gate_audit.md`. Controles declarados: `destructive_actions_added=False`, `external_publication_out_of_scope=True`.
- `FUNC-SPRINT-76` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_76_manifest.json`; audit: `docs/audits/func_sprint_76_ci_scaffolding_audit.md`. Controles declarados: `destructive_actions_added=False`, `external_publication_out_of_scope=True`, `workflow_deploys=False`, `workflow_publishes_artifacts=False`, `workflow_requires_secrets=False`.
- `FUNC-SPRINT-77` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_77_manifest.json`; audit: `docs/audits/func_sprint_77_release_manifest_audit.md`. Controles declarados: `destructive_actions_added=False`, `external_publication_out_of_scope=True`.
- `FUNC-SPRINT-78` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_78_manifest.json`; audit: `docs/audits/func_sprint_78_changelog_audit.md`. Controles declarados: `deploys_artifacts=False`, `external_api_used=False`, `publishes_artifacts=False`.
- `FUNC-SPRINT-79` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_79_manifest.json`; audit: `docs/audits/func_sprint_79_packaging_audit.md`. Controles declarados: `deploys_artifacts=False`, `dist_outputs_path=dist/`, `excludes_caches=True`, `excludes_outputs=True`, `excludes_runtime_state=True`, `external_api_used=False`.
- `FUNC-SPRINT-80` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_80_manifest.json`; audit: `docs/audits/func_sprint_80_sbom_supply_chain_audit.md`. Controles declarados: `deploys_artifacts=False`, `external_api_used=False`, `publishes_artifacts=False`.
- `FUNC-SPRINT-81` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_81_manifest.json`; audit: `docs/audits/func_sprint_81_release_verification_audit.md`. Controles declarados: `deploys_artifacts=False`, `external_api_used=False`, `publishes_artifacts=False`.
- `FUNC-SPRINT-83` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_83_manifest.json`. Controles declarados: `deploys_artifacts=False`, `external_api_used=False`, `outputs_excluded_by_default=True`, `publishes_artifacts=False`, `secret_guard_integrated=True`.
- `FUNC-SPRINT-84` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_84_manifest.json`. Controles declarados: `deploys_artifacts=False`, `external_api_used=False`, `publishes_artifacts=False`.
- `FUNC-SPRINT-86` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_86_manifest.json`. Controles declarados: `external_api_used=False`, `secret_redaction_integrated=True`.
- `FUNC-SPRINT-87` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_87_manifest.json`. Controles declarados: `external_api_used=False`, `secret_guard_integrated=True`.
- `FUNC-SPRINT-88` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_88_manifest.json`. Controles declarados: `external_api_used=False`.
- `FUNC-SPRINT-90` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_90_manifest.json`. Controles declarados: `destructive_actions_executed=False`, `external_api_used=False`.
- `FUNC-SPRINT-91` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_91_manifest.json`. Controles declarados: `destructive_actions_executed=False`, `external_api_used=False`.
- `FUNC-SPRINT-92` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_92_manifest.json`; audit: `docs/audits/func_sprint_92_advanced_evals_audit.md`. Controles declarados: `destructive_actions_executed=False`, `external_api_used=False`, `secret_leakage_cases_synthetic_only=True`.
- `FUNC-SPRINT-93` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_93_manifest.json`; audit: `docs/audits/func_sprint_93_plugin_ecosystem_audit.md`. Controles declarados: `external_api_used=False`.
- `FUNC-SPRINT-94` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_94_manifest.json`. Controles declarados: `external_api_used=False`, `secrets_read=False`.
- `FUNC-SPRINT-96` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_96_manifest.json`. Controles declarados: `external_api_used=False`, `runtime_db_exported=False`, `secrets_exported=False`.
- `FUNC-SPRINT-97` — Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint. Source: `docs/functional_sprint_97_manifest.json`. Controles declarados: `external_api_used=False`.

### References

- `FUNC-SPRINT-74` — `docs/functional_sprint_74_manifest.json`
- `FUNC-SPRINT-75` — `docs/functional_sprint_75_manifest.json`
- `FUNC-SPRINT-76` — `docs/functional_sprint_76_manifest.json`
- `FUNC-SPRINT-77` — `docs/functional_sprint_77_manifest.json`
- `FUNC-SPRINT-78` — `docs/functional_sprint_78_manifest.json`
- `FUNC-SPRINT-79` — `docs/functional_sprint_79_manifest.json`
- `FUNC-SPRINT-80` — `docs/functional_sprint_80_manifest.json`
- `FUNC-SPRINT-81` — `docs/functional_sprint_81_manifest.json`
- `FUNC-SPRINT-82` — `docs/functional_sprint_82_manifest.json`
- `FUNC-SPRINT-83` — `docs/functional_sprint_83_manifest.json`
- `FUNC-SPRINT-84` — `docs/functional_sprint_84_manifest.json`
- `FUNC-SPRINT-85` — `docs/functional_sprint_85_manifest.json`
- `FUNC-SPRINT-86` — `docs/functional_sprint_86_manifest.json`
- `FUNC-SPRINT-87` — `docs/functional_sprint_87_manifest.json`
- `FUNC-SPRINT-88` — `docs/functional_sprint_88_manifest.json`
- `FUNC-SPRINT-89` — `docs/functional_sprint_89_manifest.json`
- `FUNC-SPRINT-90` — `docs/functional_sprint_90_manifest.json`
- `FUNC-SPRINT-91` — `docs/functional_sprint_91_manifest.json`
- `FUNC-SPRINT-92` — `docs/functional_sprint_92_manifest.json`
- `FUNC-SPRINT-93` — `docs/functional_sprint_93_manifest.json`
- `FUNC-SPRINT-94` — `docs/functional_sprint_94_manifest.json`
- `FUNC-SPRINT-95` — `docs/functional_sprint_95_manifest.json`
- `FUNC-SPRINT-96` — `docs/functional_sprint_96_manifest.json`
- `FUNC-SPRINT-97` — `docs/functional_sprint_97_manifest.json`
- `FUNC-SPRINT-98` — `docs/functional_sprint_98_manifest.json`
- `FUNC-SPRINT-99` — `docs/functional_sprint_99_manifest.json`

### Policy notes

- The changelog must not invent changes outside local manifests, commits or approved docs.
- The CLI does not overwrite `docs/release/CHANGELOG.md`; report writing is limited to `outputs/reports`.
- Publication, Git tagging, signing and packaging remain outside FUNC-SPRINT-78.



## FUNC-SPRINT-98 — Remote runners experimentales y enterprise reporting

### Added

- ADR `docs/02_architecture/adrs/ADR-0017-remote-runners-experimental.md` para fijar remote runners como capacidad experimental deshabilitada por defecto.
- Registry `.devpilot/remote/runner_registry.json` y schema `docs/schemas/remote_runner.schema.json`.
- CLI `remote runner status --json` para inspección sin ejecución.
- CLI `enterprise report --json --write-report` para reporte enterprise local/read-only.
- Suite `remote-enterprise` integrada al safety gate.

### Security

- No hay ejecución remota real.
- No hay cloud control plane, red, API externa, shell, credenciales ni lectura de secretos.
- Cualquier intento futuro de ejecución requiere ADR nueva, approval, RBAC, sandboxing y evaluación ampliada.

### Evidence

- `docs/functional_sprint_98_manifest.json`
- `docs/audits/func_sprint_98_enterprise_reporting_audit.md`


## FUNC-SPRINT-99 — Industrial readiness gate y cierre Fase H

### Added

- Módulo `src/devpilot_core/industrial/readiness.py` con `IndustrialReadinessGate`.
- CLI `industrial-readiness check --json --write-report`.
- Perfil `quality-gate run --profile industrial`.
- Schema `docs/schemas/industrial_readiness.schema.json`.
- Closure report `docs/audits/phase_h_advanced_capabilities_closure.md`.
- Backlog semilla `docs/backlogs/post_phase_h_ideas.md`.

### Changed

- Fase H pasa de `in_progress` a `closed_implemented_initial`.
- README, runbook, backlog Fase H, functional backlog, MIASI y schema catalog quedan sincronizados con Sprint 99.

### Security

- El gate bloquea sobredeclarar producción cuando existen capacidades `implemented-initial` o `experimental`.
- Remote runners continúan disabled/default, sin ejecución remota, cloud, red ni APIs externas.

### Evidence

- `docs/functional_sprint_99_manifest.json`
- `docs/audits/phase_h_advanced_capabilities_closure.md`
- `docs/backlogs/post_phase_h_ideas.md`

## Historical verification anchors

This section preserves exact sprint-title anchors used by documentation regression tests. The changelog builder must follow a no invent policy: it summarizes only local sprint manifests and must not invent evidence, audits, files, decisions or outcomes not declared in repo artifacts.

- FUNC-SPRINT-93 — Plugin y connector ecosystem controlado
- FUNC-SPRINT-94 — Multiworkspace Manager y portfolio local
- FUNC-SPRINT-95 — RBAC local y modelo de identidad
- FUNC-SPRINT-96 — Colaboración local y audit packs
- FUNC-SPRINT-97 — Compliance packs y policy packs
- FUNC-SPRINT-98 — Remote runners experimentales y enterprise reporting

- FUNC-SPRINT-99 — Industrial readiness gate y cierre Fase H

## [post-h-002-d] - 2026-06-24

### Added

- `MaturityApplicationService` como frontera de aplicación para el dashboard de madurez.
- CLI `python -m devpilot_core maturity dashboard --json`.
- Escritura explícita con `--write-report` de `outputs/reports/maturity_dashboard.json` y `outputs/reports/maturity_dashboard.md`.
- Pruebas focales para ApplicationService, CLI JSON y escritura de reportes canónicos.
- Reporte de auditoría `docs/audits/post_h_002_d_cli_application_service_report.md` y manifest `docs/post_h_002_d_manifest.json`.

### Security

- No se habilita remote execution, connector write, plugin execution, APIs externas ni red.
- La escritura queda limitada a `outputs/reports` y se ejecuta solo con `--write-report`.
- No se declara producción completa, enterprise-ready, remote-ready ni compliance-certified.

### Notes

- Capacidad `implemented-initial`; el quality gate específico y cierre completo de `POST-H-002` quedan para `POST-H-002-E`.

## [post-h-002-e] - 2026-06-24

### Added

- `MaturityDashboardQualityGate` para validar el dashboard local contra schema, no-go gates, evidencia, roadmap y reportes opcionales.
- CLI `python -m devpilot_core maturity gate --json` y `--write-report`.
- Subgate `maturity-dashboard` en `quality-gate run --profile hardening` e `industrial`.
- Contract `post-h-002-maturity-dashboard` en `.devpilot/testing/test_contract_registry.json`.
- Prueba documental `tests/test_post_h_002_documentation.py`.
- Alias `schema validate --schema-id` para alinear comandos del backlog.
- Reporte `docs/audits/post_h_002_e_quality_gate_documentation_report.md`, closure report `docs/audits/post_h_002_closure_report.md` y manifest `docs/post_h_002_e_manifest.json`.

### Changed

- `POST-H-002_maturity_dashboard_local.md` pasa a `implementation_status: "closed"` y versión `1.0.0`.
- `.devpilot/project_state.json` registra `last_completed_sprint=POST-H-002` y `next_sprint=POST-H-003`.
- README y runbook quedan sincronizados con el cierre de POST-H-002.
- El audit de `POST-H-002-D` agrega `approval: "internal"` para eliminar el warning documental heredado.

### Security

- No se habilita remote execution, connector write, plugin execution, APIs externas ni red.
- El gate no muta fuentes; `--write-report` solo escribe `outputs/reports/maturity_dashboard.json` y `outputs/reports/maturity_dashboard.md`.
- No se declara producción completa, enterprise-ready, remote-ready ni compliance-certified.

### Notes

- `POST-H-002` queda cerrado como capacidad local `implemented-initial`; `production-ready-local` queda reservado para el hito final `POST-H-025`.
- El siguiente hito recomendado es `POST-H-003 — Test Contract Registry 2.0`.
