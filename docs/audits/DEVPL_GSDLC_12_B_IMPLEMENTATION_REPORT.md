---
doc_id: "DEVPL-GSDLC-12-B-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-12-B — Branch/external edit reconciliation and conflict UX implementation report"
status: "implemented-local-qualified/windows-validation-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-12"
approval: "pending-windows-validation"
---

# Objetivo

Implementar GSDLC-12-B sobre repo426 sin Git destructivo ni pérdida de trabajo, manteniendo FRX v2.4 y Full Regression=0 en este micro-sprint.

# Fuente de ejecución

- Repo: `repo_DevPilot_Local_426_DEVPL_GSDLC_12_A_PERSISTENT_RESUMABILITY_RECOVERY_LOCKS_WINDOWS_VALIDATED_CANDIDATE.zip`.
- Commit: `f79f5d32c928247039feeecb9c773b75343b6a2e`.
- SHA-256: `b366fd4587bc057e8330fa419c7972fcdec6a8daaf66acd00b587da88f89bf66`.
- 12-A: `CLOSED/PASS/WINDOWS-VALIDATED`.

# Implementación

`AdvancedWorkspaceReconciliationService` observa Git/filesystem en modo read-only y mantiene un baseline explícito bajo `outputs/workspaces/<workspace>/reconciliation/baseline.json`. La captura/adopción del baseline es dry-run por defecto, exige confirmación tipada, usa `WorkspaceLockService` de 12-A y vuelve a verificar identidad Git y limpieza después de adquirir el lock. Ninguna operación modifica el managed workspace ni Git.

Se detectan branch switch, detached HEAD, fast-forward, rewind, divergence, dirty tracked, untracked relevante, modify/add/delete/rename. La clasificación es `NO_CONFLICT`, `REVALIDATE`, `REPLAN_REQUIRED`, `MANUAL_RECONCILIATION_REQUIRED` o `READ_ONLY_BLOCK`. Un cambio de autoridad invalida approval/preimage/plan para impedir reutilización stale. Los draft refs del checkpoint de 12-A se conservan y se proyecta un recovery plan seguro.

API: `GET /api/v1/reconciliation`, `POST /api/v1/reconciliation/baseline`, `POST /api/v1/reconciliation/adopt`. UI: `ConflictResolutionView` `/reconciliation` y sección explícita en Project Status. API/RBAC/OpenAPI/UI registries y TCR v1/v2 fueron reconciliados conjuntamente.

# Drift current-active corregido

1. `source_registry.gsdlc_last_registered_micro_sprint` heredado de 11-E se reconcilia a 12-B.
2. Se retira el sensitive action duplicado `recovery.lock.recover_stale`; la autoridad vigente es la ruta server-side de 12-A + confirmación tipada + roles.
3. `ui_capability_registry.ui_routes` se reconcilia con la colección viva, incorpora `ui.recovery` faltante y `ui.reconciliation`; contadores derivados se recalculan.
4. El inventario canónico FastAPI y `openapi_v1.json` se reconcilian con las rutas Recovery de 12-A y Reconciliation de 12-B; POST-H-014/028 vuelve a operar sobre la superficie API vigente.

# Pruebas locales ejecutadas

- Focal backend/contracts/transport 12-B: `19 passed / 0 failed / 0 errors / 0 skipped`.
- Suite acumulativa/impactada (12-B + 12-A + API security/route drift + Project State + TCR v2 + Test Impact + schema registry): `122 passed / 0 failed / 0 errors / 0 skipped`.
- API route/OpenAPI corrective retest: `19 passed / 0 failed / 0 errors / 0 skipped`.
- UI smoke 12-B: `11/11 PASS`.
- Test Impact v2: `43 changed paths / 217 matched contracts / 339 recommended tests / 0 unmatched paths`.
- Gates determinísticos: Project State PASS; Docs Governance PASS; TCR v1 PASS; TCR v2 PASS; API Route Contract Registry PASS; API Contract Drift PASS.
- Full Regression: `0`; budget GSDLC-12 permanece `0/1` reservado para 12-E.

# Riesgos y limitaciones

- La aceptación real-browser Windows sigue pendiente y es obligatoria para cerrar 12-B.
- La reconciliación no intenta resolver automáticamente un merge/divergence; lo presenta como manual reconciliation para evitar pérdida de datos.
- Baseline/adoption solo actualiza metadata de autoridad; el usuario debe resolver los cambios Git/source explícitamente fuera de esta operación.
- Esta es la primera versión industrial de conflict UX; performance/security red-team global corresponde a 12-D.

# Criterios PASS/BLOCK

**PASS local:** focal + acumulativa impactada + contratos/gates + UI smoke PASS, Test Impact sin paths huérfanos, source/Git mutation=0, Full=0, S0/S1=0 y registries current-active coherentes.

**PASS Windows:** además, browser real demuestra como mínimo un conflicto `REVALIDATE` y otro `MANUAL_RECONCILIATION_REQUIRED`, con diff/resumen visible, drafts preservados y evidencia de ausencia de Git destructivo.

**BLOCK:** overwrite silencioso, Git destructivo automático, adopción dirty/stale, aprobación/preimage/plan stale ejecutable, conflicto oculto, pérdida de drafts, S0/S1 abierto o ejecución de Full en 12-B sin hard trigger owner-approved.

# Comandos de verificación

`python -m pytest -p no:ddtrace --assert=plain -q tests/test_devpl_gsdlc_12_b_reconciliation.py tests/test_devpl_gsdlc_12_b_reconciliation_contracts.py tests/test_devpl_gsdlc_12_b_reconciliation_transport.py`

`node ui/web/scripts/gsdlc12b-reconciliation-smoke.mjs`

`python -m devpilot_core project-state validate --json`

`python -m devpilot_core docs-governance validate --json`

`python -m devpilot_core test-contracts validate-v2 --json`

`python -m devpilot_core api contract-drift --json`
