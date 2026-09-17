---
doc_id: "DEVPL-UX-P0-C-IMPLEMENTATION-REPORT"
title: "DEVPL-UX-P0-C — Greenfield critical-path surface productization implementation report"
status: "IMPLEMENTED/LOCAL-QUALIFIED/WINDOWS-VALIDATION-PENDING"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
source_repo: "repo_DevPilot_Local_433_DEVPL_UX_P0_B_PROJECT_CONTEXT_AUTH_SCOPE_CORRECTIVE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "dc63672f2d617968998f3c68374a03581b348578"
source_repo_sha256: "f4415775bd3bf5a01b6368197d0754374de93b659fa5f6bbff8b7a2b8ead4246"
successor_expected: "repo_DevPilot_Local_434_DEVPL_UX_P0_C_GREENFIELD_CRITICAL_PATH_WINDOWS_VALIDATED_CANDIDATE.zip"
full_regression_runs: 0
---

# DEVPL-UX-P0-C — Implementation report

## Alcance implementado

UX-P0-C productiza el primer tramo del piloto greenfield sin cambiar paths, route IDs, RBAC, approvals ni autoridad server-side. El cambio es presentation/copy/action-hierarchy sobre Home, Project Entry, Project Status, Pre-code, Documents entry/overview y Planning.

### Project Home

- `CREATE_NEW` queda como acción primaria inequívoca.
- `OPEN_EXISTING` e `IMPORT_GIT` permanecen alternativas explícitas.
- se incorpora `Retomar proyecto activo` mediante la recuperación server-authoritative ya probada en B (`/project/status?recover_project_context=server-active`), resolviendo el UX-S2 heredado sin convertir browser storage en autoridad.

### Project Entry

Se presenta el ciclo `Parámetros → Dry-run → Revalidar → Approval → Ejecutar → Verificar` y se explica el efecto de aprobación antes de cualquier mutación. Los contratos dry-run, preimage, approval y execute existentes no se alteran.

### Project Status

Se añade guía de critical path con stage/progress, blocker explanation, siguiente acción y recovery. Los reason codes y datos técnicos continúan disponibles mediante progressive disclosure; no se eliminan.

### Pre-code

La secuencia obligatoria de siete etapas permanece intacta. La UI explica etapa actual, ready/block y siguiente acción; los datos MIASI/authority crudos quedan disponibles como detalle técnico, no como copy primario Guided.

### Documents

Se añade una orientación de entrada `Buscar → Revisar → Draft → Validar → Aplicar` y se conserva el workbench/editor existente sin refactor profundo.

### Planning

Roadmap → Backlog → Sprint se presenta como jerarquía explícita. La edición JSON técnica permanece disponible tras disclosure y la jerarquía de acciones diferencia primary/secondary sin cambiar endpoints ni lifecycle.

## Primitives

Se introduce `CriticalPathGuidance.ts` como primitive de presentación reutilizable. No es un nuevo router ni autoridad de workflow.

## Reconciliación de contratos heredados

Se evolucionaron únicamente contratos/tests current-active stale:

- test B successor-aware conserva la evidencia de cierre de B al avanzar C;
- fixture GSDLC-05-E usa el canonical project id establecido por el correctivo B para MIASI/RBAC;
- workspace documents acepta el target mínimo 44 px expresado mediante semantic token introducido en UX-P0-A;
- smokes históricos Project Entry/Roadmap aceptan el wording successor actual sin rebajar invariantes.

Los contratos históricos congelados no se reescriben.

## Seguridad y autoridad

- Full Regression: `0` (prohibida en C).
- no remote push/publish/deploy.
- no dependencia frontend nueva.
- server authority/RBAC/approvals preservados.
- no terminal escape agregado al normal journey.
- LF/CRLF no se usa como autoridad de delta.

## Estado de madurez

Esta es una productización **preliminar y acotada pre-piloto**, no la UI industrial final. UX-P0-D aún debe normalizar patrones operacionales cross-surface y UX-P0-E debe cerrar browser/usability/a11y/performance y la única Full del backlog.


## Reconciliación final de Evidence Freshness

El gate final identificó un único current-active stale en `project-state-current-repo`: `local_release_candidate_criteria` todavía esperaba UX-P0-B/repo432 mientras Project State ya estaba legítimamente en UX-P0-C/repo434. Se evolucionó únicamente ese criterio current-active y el Source Registry (`current_micro_sprint=C`, `next_micro_sprint=D`), preservando snapshots históricos. El rerun final cerró `PASS`, con 49 evidencias, 48 fresh y `critical_stale/missing/invalid = 0/0/0`.
