---
doc_id: "ADR-GSDLC-008"
title: "External artifact drift is reconciled, never auto-reverted"
status: "accepted/pending-windows-proof"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-22"
approval: "pending_windows_proof"
---

# ADR-GSDLC-008 — External artifact drift is reconciled, never auto-reverted

## Contexto

GSDLC-04-E debe permitir convivencia segura entre el Artifact Workbench y ediciones realizadas fuera de DevPilot (VS Code, Git u otro editor local). Un artefacto `APPROVED/FROZEN` no puede permanecer aprobado si su contenido cambia, pero DevPilot tampoco puede sobrescribir silenciosamente el trabajo externo.

## Decisión

Extender `ArtifactLifecycleService` y `ArtifactReviewApplicationService` como autoridades existentes para detectar `modified`, `renamed` y `deleted`, mover el artefacto a `REVALIDATION_REQUIRED`, invalidar el approval previo y conservar evidencia de provenance/Git. La UI `ArtifactReconciliationUX` presenta el cambio y su diff sin auto-revert, hidden merge ni source write.

La detección de rename usa coincidencia exacta del hash aprobado dentro del workspace gobernado; una coincidencia ambigua no se adivina y se clasifica conservadoramente como delete hasta nueva revisión humana. Git se consulta solo por argv nativo y `shell=False` implícito; no se ejecutan checkout, reset, clean, merge, rebase, push ni comandos suministrados por el usuario.

## Razones

- protege el hash congelado como authority de aprobación;
- respeta ediciones externas en vez de revertirlas;
- evita un segundo motor de escritura/reconciliación;
- mantiene el browser como UX y el server como authority;
- hace visible branch/status/diff/provenance para diagnóstico.

## Consecuencias

Una edición externa invalida approval/freeze y requiere un nuevo ciclo de DRAFT → validate → approval → apply/freeze. Rename/delete se detectan sin mutar source. El branch switch se registra como contexto; no se hace switch automático ni hidden merge.

## Alternativas descartadas

- Auto-revert al hash aprobado: descartado por riesgo de pérdida de trabajo externo.
- Merge automático: descartado por authority y conflict resolution implícitos.
- Reconciliación únicamente cliente-side: descartada porque lifecycle/approval son server-authoritative.

## Verificación

`tests/test_devpl_gsdlc_04_e_external_reconciliation.py`, smoke UI 04-E, browser acceptance de cierre y la full regression única de GSDLC-04 en Windows.
