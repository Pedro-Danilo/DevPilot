---
doc_id: "DEVPL-GSDLC-11-C-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-11-C — Install, upgrade and rollback workflows implementation report"
status: "implemented/local-qualified/windows-validation-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-11"
approval: "local_qualified/windows_pending"
---

# 1. Objetivo

Implementar clean install, upgrade gobernado con backup obligatorio y rollback verificable desde una UI project-scoped, usando exclusivamente un sandbox local controlado y componiendo la maquinaria existente de package/install/backup/upgrade/rollback.

# 2. Baseline y política FRX-v2.4

- Fuente de ejecución: `repo_DevPilot_Local_422_DEVPL_GSDLC_11_B_REPRODUCIBLE_PACKAGE_SBOM_WINDOWS_VALIDATED_CANDIDATE.zip`.
- Commit: `836145a853fbae502f58e43b1cdab5126983a987`.
- SHA-256: `f6285bb75e79873f594f8edc47621c113a8100c301af4ff1ef64bcf01700c23c`.
- GSDLC-11-B permanece `CLOSED/PASS/WINDOWS-VALIDATED`.
- GSDLC-11-C usa focal + acumulativa + Test Impact; Full Regression = **0**.
- Budget de GSDLC-11: **0/1**, reservado para 11-E salvo hard trigger owner-approved.
- Historical facts se congelan; current-active pointers evolucionan por successor contracts.

# 3. Arquitectura implementada

`ReleaseLifecycleApplicationService` expone operaciones tipadas `status`, `install.plan/execute`, `upgrade.plan/execute` y `rollback.plan/execute`. La autoridad de entrada es el package reproducible commit/tree-bound de 11-B. La mutación queda restringida a `outputs/release/gsdlc11c/controlled-install-target`; source, Git y datos de producción permanecen inmutables.

Clean install valida SHA-256 del package, safe extraction, versión y capability mínima. Upgrade exige backup ZIP determinístico + manifest/hash antes de la fault injection controlada. Rollback se separa en dry-run/execute y solo adjudica PASS con restore tree hash exacto, marker de fallo ausente y capability mínima restaurada.

# 4. API/UI y autoridad

- API project-scoped: status + seis operaciones plan/execute.
- `owner` / `release-manager` para mutaciones.
- UI `/release/lifecycle` con secuencia explícita package prerequisite → install → backup/upgrade → rollback.
- Browser/storage no son autoridad.
- No arbitrary shell, publish, deploy, tag, package-manager ni red.

# 5. Reentrancia y seguridad

Receipts PASS se reutilizan solo cuando input authority/hash permanece íntegro. Se corrigió el orden de revalidación del upgrade para permitir recovery después de una interrupción `ROLLBACK_REQUIRED`. El capability probe ejecuta Python con bytecode deshabilitado para no contaminar el tree hash restaurado con `__pycache__`.

# 6. Reconciliación contractual

- UI route source markers reconciliados en `client.ts` y `types.ts`.
- TCR v2 usa profile `release` y safety exception owner-approved limitada al sandbox.
- Test Impact registry conserva `mutations_allowed=false` porque el analizador es read-only; la mutación controlada pertenece a los tests seleccionados, no a la regla.
- El contrato 11-B se convirtió en historical-freeze sobre hechos de cierre/successor; dejó de pinnear punteros current-active a repo421/11-B.
- Local release criteria se rebindeó a repo422/11-C.

# 7. Validación local acreditada

- GSDLC-11-C funcional/contract: **6/6 PASS**.
- Installation plan + backup/upgrade + POST-H-027 upgrade/rollback + Windows install + POST-H-026 install smoke: **32/32 PASS**.
- API security/contract/drift/UI route enforcement: **42/42 PASS**.
- GSDLC-11-B cumulative/historical contract: **9/9 PASS**.
- UI static smoke GSDLC-11-C: **8/8 PASS**.
- Project State, Documentation Governance, TCR v1, TCR v2: **PASS**.
- Test Impact Rules: **PASS**.
- Full Regression: **0**.

# 8. Riesgos y limitaciones

1. Esta es una primera versión local/sandbox-only: no es instalador system-wide ni workflow productivo de migración de datos.
2. La fault injection es deliberadamente artificial y solo sirve para demostrar rollback en target desechable.
3. No se ejecutan pip/npm installers ni servicios externos desde el sandbox.
4. La aceptación Windows/browser debe demostrar el normal journey y no puede ser sustituida por el operador.
5. Targets no-sandbox, migraciones reales, health checks de servicios instalados y políticas de backup productivo requieren evolución futura.

# 9. PASS/BLOCK

**PASS local:** contratos/guards/UI/Test Impact sin S0/S1 y Full=0.

**PASS Windows pendiente:** browser real + package prerequisite + clean install PASS + backup-before-upgrade + controlled fault + rollback exact restore + evidence + clean Git + repo423 package.

**BLOCK:** package authority/hash stale, upgrade sin backup, restore no verificado, mutación fuera del sandbox, role/scope bypass, network/publish/deploy, S0/S1 o Full ejecutada en 11-C.
