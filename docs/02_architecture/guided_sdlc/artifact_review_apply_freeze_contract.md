---
doc_id: "DEVPL-GSDLC-04-D-ARTIFACT-REVIEW-APPLY-FREEZE-CONTRACT"
title: "GSDLC-04-D — Governed artifact review, apply and freeze contract"
status: "implemented/ready-for-windows"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-22"
approval: "pending_windows_proof"
---

# Governed artifact review, apply and freeze contract

## 1. Objetivo

Unificar `validate → findings → immutable plan/diff → exact approval → preimage recheck → atomic apply → freeze → transition evidence` sin crear un segundo write engine.

## 2. Autoridades

- ArtifactProfile selecciona validadores; la UI no hardcodea una lista de authority validators.
- Human Session, Server RBAC, PolicyEngine y ApprovalStore son server-authoritative.
- El plan se materializa mediante `WorkspaceEditPlanApplicationService`.
- El único source writer es `WorkspaceEditExecutionApplicationService`, heredado de UOC-005.
- El lifecycle continúa en `ArtifactLifecycleService`.
- Los DRAFT records sellados de 04-B/04-C permanecen evidencia histórica; 04-D mantiene successor review/lifecycle state separado.

## 3. Estado y transición

`DRAFT → VALIDATING → FINDINGS | READY_FOR_REVIEW → APPROVAL_REQUIRED → APPROVED → FROZEN`.

Un cambio posterior de hash desde `APPROVED/FROZEN` produce `REVALIDATION_REQUIRED` e invalida la reutilización de approval.

## 4. Change plan

Todo plan registra `plan_id`, `plan_hash`, target exacto, `document_sha_before`, proposed hash/content, operation `create|modify`, diff completo y side-effects explícitos. Para create, la preimage ausente se representa con SHA-256 cero y se revalida inmediatamente antes de approval/apply.

## 5. Apply/rollback

- approval exacto ligado a plan/hash/base/actor;
- preimage, actor y sesión se revalidan antes de escribir;
- backup externo para modify;
- atomic temp + replace para source write;
- failure injection soporta compensating rollback;
- create fallido vuelve a preimage ausente; modify fallido restaura backup;
- ningún Git stage/commit forma parte del write engine.

## 6. Findings navigation

Findings conservan `line` y/o `section` cuando el validador puede resolverlos. La UI expone navegación segura al editor MANUAL mediante un evento UX que solo reposiciona el textarea; no altera authority ni source.

## 7. Freeze evidence

Freeze exige ejecución aplicada exacta, plan/hash exactos, actor/session válidos y hash source actual igual al aprobado. Registra hash aprobado y transition evidence sin secretos.

## 8. Seguridad

Deny-by-default, no shell, no network, no external API, no pilot workspace, no approval supplied as authority by browser storage, no hidden merge y no segundo motor de escritura.

## 9. PASS/BLOCK

**PASS:** APPROVED/FROZEN solo con validation + approval; rollback consistente; write únicamente target declarado; S0/S1=0; full=0.

**BLOCK:** approval bypass/reuse, stale preimage, partial write, wrong-role promotion, runtime DB copied, unregistered API/UI authority o source writer alterno.
