---
doc_id: "ADR-GSDLC-007"
title: "Reuse UOC-005 atomic document writer for governed artifact promotion"
status: "accepted/pending-windows-proof"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-22"
approval: "pending_windows_proof"
---

# ADR-GSDLC-007 — Reuse UOC-005 atomic document writer for governed artifact promotion

## Contexto

GSDLC-04-D debe promover DRAFTs validados a source aprobado. UOC-005 ya posee el boundary de escritura gobernada con approval exacto, preimage recheck, backup, atomic replace y rollback.

## Decisión

Extender el planner/executor existente para soportar `create` además de `modify`, manteniendo `WorkspaceEditExecutionApplicationService` como único write engine. El review/lifecycle successor vive en `ArtifactReviewApplicationService` y no modifica retroactivamente los DRAFT records estrictos de 04-B/04-C.

## Razones

- evita dos motores de escritura y drift de seguridad;
- conserva SensitiveAction/RBAC/MIASI ya existentes para `filesystem.workspace_document_apply`;
- centraliza stale-preimage y rollback;
- permite demostrar create/modify bajo el mismo contrato.

## Consecuencias

El executor incorpora preimage ausente determinística (`ZERO_SHA256`) y rollback compensatorio por eliminación solo para un target creado por la misma ejecución. External edit reconciliation completo sigue perteneciendo a 04-E.

## Alternativas descartadas

Crear `ArtifactApplyEngine` paralelo: rechazado por duplicar authority, backups, approval y rollback. Escribir desde UI/import service: rechazado por bypass de ApplicationService/Policy/Approval.

## Riesgos

Create-new amplía el writer existente y requiere pruebas negativas de target aparecido, wrong approval, injected failure y path scope. La aceptación Windows debe usar fixture desechable y demostrar que solo cambia el artifact declarado.

## Verificación

`tests/test_devpl_gsdlc_04_d_artifact_review_apply_freeze.py` + contratos UOC-004/UOC-005 + browser acceptance 04-D. Full regression queda reservada para 04-E.
