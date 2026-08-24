---
doc_id: "DEVPL-GSDLC-04-E-ARTIFACT-EXTERNAL-RECONCILIATION-CONTRACT"
title: "GSDLC-04-E — External artifact reconciliation and browser closure contract"
status: "implemented/ready-for-windows"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-22"
approval: "pending_windows_proof"
---

# External artifact reconciliation contract

## 1. Objetivo

Cerrar Artifact Workbench demostrando convivencia segura con editores externos/Git y el lifecycle completo desde autoría/importación hasta `FROZEN` y posterior `REVALIDATION_REQUIRED` cuando cambia el source aprobado.

## 2. Authority

- Human Session + Server RBAC + Policy + Approval permanecen autoridad.
- `ArtifactLifecycleService` gobierna la transición por drift.
- `ArtifactReviewApplicationService` correlaciona review/freeze/provenance/Git.
- `WorkspaceEditExecutionApplicationService` UOC-005 sigue siendo el único writer de promociones gobernadas.
- `sessionStorage/localStorage` siguen siendo UX-only.

## 3. Detección externa

Para reviews `APPROVED/FROZEN`:

- `modified`: target existe y su hash difiere del aprobado;
- `renamed`: target original no existe y existe exactamente un Markdown/JSON con el hash aprobado;
- `deleted`: target original no existe y no existe rename exacto no ambiguo.

Un cambio real produce `REVALIDATION_REQUIRED`, `approval_valid=false`, provenance `EXTERNAL_EDITOR` y lineage de reconciliación. Un source sin drift conserva `FROZEN` y approval válido.

## 4. Git/provenance UX

La evidencia de reconciliación expone branch al freeze, branch actual, branch_changed, status porcelain, Git diff y source provenance. La UI no lee filesystem directamente; consume la API local protegida y renderiza mediante DOM seguro.

## 5. No-go

- no auto-revert;
- no hidden merge;
- no checkout/switch/rebase/reset/clean/push;
- no approval reuse después de drift;
- no source write desde reconciliation;
- no piloto real como fixture;
- no network/external API.

## 6. Browser closure

El cierre Windows cubre project context/guard, MANUAL Markdown/JSON, autosave/restart, PASTE, UPLOAD/IMPORT, negativos, findings/navigation, immutable plan/diff, owner approval, wrong-role denial, apply/freeze, stale preimage, external drift/revalidation, rollback/recovery, API-down recovery y accesibilidad.

Normal user PowerShell requerido = 0; external operator project writes = 0.

## 7. Full regression

Después de los gates baratos, Contract Reconciliation Sweep y browser acceptance PASS, se crea un marker durable y se ejecuta exactamente una full regression para GSDLC-04. Si falla, el log/JUnit/marker quedan sellados, no se repite la full y solo se permite exact failed-nodeid retest + bounded impact + Historical Regression Guard para formar composite evidence.
