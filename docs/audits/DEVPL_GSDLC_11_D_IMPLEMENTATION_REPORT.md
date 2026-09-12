---
doc_id: "DEVPL-GSDLC-11-D-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-11-D — Version, release notes, tag and approval implementation report"
status: "implemented-local-qualified"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-12"
approval: "pending_windows_validation"
---

# Resultado

Estado local: **IMPLEMENTED / LOCAL-QUALIFIED / WINDOWS-VALIDATION-PENDING** sobre repo423. GSDLC-11-C está previamente adjudicado CLOSED/PASS/WINDOWS-VALIDATED.

# Capacidad implementada

- `VersionDecision` SemVer fail-closed y alineado con `pyproject.toml` + evidencia package local.
- release notes derivadas de commits/evidence refs con provenance MANUAL o AGENT_ASSISTED; proposal authority=false.
- `TagPlan` dry-run exact-commit, notes-hash/version-decision-hash bound.
- release approval server-side para owner/release-manager, TTL y binding exacto al plan.
- annotated local tag únicamente tras approval válido; existing-tag conflict bloquea; tag→commit y tipo annotated verificados.
- UI `Version / tag` explicable y project-scoped.
- no push, publication, deploy, network ni API externa.

# Política FRX-v2.4

11-D usa focal + bounded cumulative + HCA/Contract Reconciliation. **Full Regression = 0**. La única logical Full de DEVPL-GSDLC-11 permanece 0/1 y reservada para 11-E. Drift documental current-active se corrige aquí sin reescribir evidencia histórica sellada.

# Corrective Windows de transporte — v1.0.4

La aceptación browser Windows detectó un gap funcional antes del cierre: las cinco rutas `/api/v1/release/metadata*` estaban presentes en router/OpenAPI/API registry y server RBAC, pero faltaban en `API_ROUTE_POLICIES` del middleware LocalAPI. El middleware fail-closed respondió correctamente `API_POLICY_BINDING_MISSING_BLOCK` (HTTP 403) antes de invocar `ReleaseMetadataApplicationService`.

El corrective v1.0.4 agrega los cinco bindings de PolicyEngine en `src/devpilot_core/interfaces/api/security.py` y una prueba dedicada de paridad transporte/API registry/server RBAC. No se relaja seguridad, no se habilita legacy token y no se consume Full Regression. Test Impact corregido: `34/203/316/0`.

# Riesgos / limitaciones

1. Esta es la primera versión industrial local de metadata/tag; publicación/remoto siguen fuera de alcance.
2. Un `v<version>` preexistente bloquea deliberadamente; no se mueve ni elimina automáticamente.
3. El tag local se prueba sobre el commit exacto del repo Windows después de aplicar/committear el delta; la evidencia local Linux no sustituye browser Windows.
4. Agent-assisted notes en esta versión aceptan una propuesta ya suministrada; no llama modelos externos y no concede authority.

# PASS

- versión/package/tag coherentes; provenance completa; approval autorizado/hash-bound; annotated tag exacto; browser PASS; focal/cumulative/HCA/Contract PASS; S0/S1=0; Full=0; no push/publication.

# BLOCK

- version drift; tag conflict; dirty tracked Git; aprobación ausente/expirada/hash mismatch; role no autorizado; tag no annotated o commit mismatch; provenance incompleta; browser BLOCK; cualquier push/publication; Full ejecutada en 11-D.

# Comandos de verificación local

`PYTHONPATH=src pytest -q tests/test_devpl_gsdlc_11_d_release_metadata.py tests/test_devpl_gsdlc_11_d_release_metadata_contracts.py tests/test_devpl_gsdlc_11_c_release_lifecycle.py tests/test_devpl_gsdlc_11_c_release_lifecycle_contracts.py`

`cd ui/web && npm run test:release-metadata`
