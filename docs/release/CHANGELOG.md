---
title: "DevPilot Local — Changelog"
doc_id: "DEVPL-RELEASE-CHANGELOG-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-G-PRODUCTIZACION-RELEASE"
sprint: "FUNC-SPRINT-78"
updated: "2026-06-17"
approval: "approved_by_owner_direction"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---

# Changelog

All notable changes to DevPilot Local are documented in this file.

This file follows a Keep a Changelog-compatible structure. Its current baseline is generated from local sprint manifests and does not replace future packaging, SBOM, checksums, signature, tag or publication evidence.

## [0.1.0] - 2026-06-17

Release ID: `DEVPL-0.1.0`  
Range: `FUNC-SPRINT-74` → `FUNC-SPRINT-78`  
Source: `docs/functional_sprint_*_manifest.json`

### Added

- `FUNC-SPRINT-74` — Release/versioning/productization strategy: ADR, release policy, artifact matrix, audit and functional manifest.
- `FUNC-SPRINT-75` — Unified local Quality Gate with `fast/full/ci` evolution path and optional reports.
- `FUNC-SPRINT-76` — Local CI profile and optional GitHub Actions scaffolding without secrets, publication or deployment.
- `FUNC-SPRINT-77` — Release Manifest generator with SemVer metadata, Git metadata, components, required evidence and release artifact expectations.
- `FUNC-SPRINT-78` — Evidence-driven changelog generator and operational change policy.

### Changed

- README, runbook, Fase G backlog and functional backlog were synchronized to the current Fase G progression.
- Release Manifest expected artifacts were extended to include the human-readable changelog evidence introduced by Sprint 78.
- Historical sprint documentation tests were synchronized with the current global milestone markers.

### Deprecated

- No entries declared by local sprint manifests for this category.

### Removed

- No entries declared by local sprint manifests for this category.

### Fixed

- No entries declared by local sprint manifests for this category.

### Security

- Fase G release flow remains local-first and dry-run-first.
- CLI changelog generation does not call network, external APIs, GitHub, GitLab, PyPI or LLMs.
- CLI changelog generation does not publish, deploy, sign artifacts, tag Git or overwrite source files; no publica artefactos externos y no despliega servicios.
- Runtime state, outputs, caches and secrets remain excluded from release packaging policy.

### References

- `docs/functional_sprint_74_manifest.json`
- `docs/functional_sprint_75_manifest.json`
- `docs/functional_sprint_76_manifest.json`
- `docs/functional_sprint_77_manifest.json`
- `docs/functional_sprint_78_manifest.json`
- `docs/05_operations/change_policy.md`
- `docs/audits/func_sprint_78_changelog_audit.md`

### Policy notes

- The changelog must not invent changes outside local manifests, commits or approved docs; no debe inventar cambios no evidenciados.
- The CLI does not overwrite this file; report writing is limited to `outputs/reports`.
- Publication, Git tagging, signing and packaging remain outside `FUNC-SPRINT-78`.
