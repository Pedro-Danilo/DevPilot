---
doc_id: DEVPL-RELEASE-CHANGELOG
title: DevPilot Local — Changelog
status: approved
version: 0.1.0
owner: Ordóñez
updated: 2026-06-17
approval: internal
---

# Changelog

## Estado

Documento canónico aprobado para changelog local de DevPilot.

## Propósito

Registrar cambios notables trazables a manifests funcionales y documentos aprobados.

All notable changes to DevPilot Local are documented in this file.

This changelog follows a Keep a Changelog-compatible category structure and is generated from local sprint manifests.

## [0.1.0] - 2026-06-17

Release ID: `DEVPL-0.1.0`  
Range: `FUNC-SPRINT-74` → `FUNC-SPRINT-84`  
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

### Deprecated

- No entries declared by local sprint manifests for this category.

### Removed

- No entries declared by local sprint manifests for this category.

### Fixed

- `FUNC-SPRINT-75` — Se registró una corrección soportada por el manifest funcional del sprint. Source: `docs/functional_sprint_75_manifest.json`; audit: `docs/audits/func_sprint_75_quality_gate_audit.md`. quality-gate run --json returns a parseable CommandResult.; Subgates include readiness, standards, MIASI, eval fixture readiness and app contract.; +3 criterios adicionales
- `FUNC-SPRINT-78` — Se registró una corrección soportada por el manifest funcional del sprint. Source: `docs/functional_sprint_78_manifest.json`; audit: `docs/audits/func_sprint_78_changelog_audit.md`. Changelog is human-readable and Keep a Changelog-compatible.; Changelog is generated from local manifests and includes traceability to sprint manifests.; +4 criterios adicionales

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

### Policy notes

- The changelog must not invent changes outside local manifests, commits or approved docs; no debe inventar cambios sin evidencia local.
- The CLI does not overwrite `docs/release/CHANGELOG.md`; report writing is limited to `outputs/reports`.
- Publication, Git tagging, signing and external deployment remain out of scope for Fase G; Sprint 84 only adds ReleaseAgent dry-run and formal closure evidence.
