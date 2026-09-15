---
doc_id: "DEVPL-POST-GSDLC-TRANSITION-DECISION"
title: "DevPilot — Post-GSDLC transition, repository authority and pilot strategy decision"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "approved_by_owner"
target_path: "docs/00_product/DEVPL_POST_GSDLC_TRANSITION_DECISION_v1_0_0_APPROVED.md"
source_repo: "repo_DevPilot_Local_430_DEVPL_GSDLC_12_E_LOCAL_RC_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "a415504bbf021566243ef4000b1a27d4c8846fee"
source_repo_sha256: "969f7d6b8cbdd8eb3bc32491718e94ee41295647e82234779aee180cea2a388a"
decision_scope: "post-GSDLC transition / remote synchronization / immutable closure baseline / UX productization / pilot rebaseline"
local_first: true
dry_run_default: true
---

# DevPilot — Post-GSDLC transition decision

## 1. Propósito

Formalizar el cambio de fase posterior al cierre `DEVPL-GSDLC-12 = CLOSED/PASS/WINDOWS-VALIDATED` y evitar que decisiones de alto impacto queden únicamente en conversaciones operativas.

Este documento no modifica el cierre de GSDLC-12 ni reescribe repo430. Su aprobación autoriza la preparación de successors y backlogs posteriores.

## 2. Autoridad de entrada

| Autoridad | Valor |
|---|---|
| Closure repo | `repo_DevPilot_Local_430_DEVPL_GSDLC_12_E_LOCAL_RC_WINDOWS_VALIDATED_CANDIDATE.zip` |
| Closure commit | `a415504bbf021566243ef4000b1a27d4c8846fee` |
| Closure SHA-256 | `969f7d6b8cbdd8eb3bc32491718e94ee41295647e82234779aee180cea2a388a` |
| GSDLC-12 | `CLOSED/PASS/WINDOWS-VALIDATED` |
| Full | `1/1`, segunda Full `0` |
| RC clean-install | `PASS/14-of-14` |

## 3. Decisiones aprobadas

### D1 — Congelar repo430 como closure artifact inmutable

`repo430` se conserva exactamente como fue cerrado y hash-bound. No se modifica para corregir drift documental posterior.

**Rationale:** repo430 está ligado a browser evidence, Full/composite recovery, RC manifest, clean-install, Git commit y SHA-256. Alterarlo degradaría la trazabilidad del cierre.

**PASS:** repo430 permanece byte-identical al SHA registrado.

**BLOCK:** volver a empaquetar contenido distinto bajo el mismo identificador repo430.

### D2 — Corregir el drift documental S3 únicamente en un successor

Los drifts current-active detectados tras el cierre —incluyendo metadata global obsoleta de `gsdlc_status`, `gsdlc_program_status`, frontmatter del backlog y campos equivalentes— se clasifican `S3/documentation-current-authority-hygiene`.

Se corrigen en el siguiente successor natural, sin reabrir GSDLC-12 y sin crear un corrective repo430.

### D3 — Sincronizar Git local con remoto

El branch local `official/devpilot-local`, actualmente adelantado respecto a `origin/official/devpilot-local`, debe sincronizarse después de un `fetch` y una comprobación explícita de ausencia de divergencia remota.

Condición de promoción:

```text
local ahead > 0
remote behind local = true
official worktree clean
HEAD = a415504bbf021566243ef4000b1a27d4c8846fee o successor owner-approved
push = normal fast-forward
force push = prohibited
```

Se recomienda crear un annotated milestone tag del cierre GSDLC-12 después de confirmar la sincronización.

### D4 — Separar aceptación greenfield de migración legacy

La próxima evaluación de producto se divide en dos objetivos distintos:

1. **Greenfield Product Acceptance:** crear software real desde cero usando DevPilot como flujo normal.
2. **Legacy Adoption Acceptance:** posteriormente reabrir/adoptar el `inventory-sales-local` histórico para probar import/reconciliation/migration.

No se mezclan ambos objetivos en una misma corrida porque miden capacidades diferentes.

### D5 — Introducir una fase UX acotada antes del piloto greenfield

No se ejecuta un rediseño total antes del piloto. Se implementa primero una base UX/productization limitada al shell y al critical path; el resto se corrige con evidencia del piloto y se consolida después.
 
La política vinculante se define en `DEVPL_UI_UX_PRODUCTIZATION_STRATEGY_v1_0_0_APPROVED.md`.

## 4. Orden de transición recomendado

```text
GSDLC-12 CLOSED/PASS
→ freeze repo430
→ git fetch + divergence check
→ push fast-forward + milestone tag
→ successor documental/rebaseline
→ UX foundation bounded wave
→ greenfield E2E pilot
→ pilot-driven UX correctives
→ independent acceptance
→ legacy adoption/migration pilot
→ next product roadmap from observed gaps
```

## 5. No-go

- no modificar repo430;
- no force push;
- no reejecutar la Full de GSDLC-12;
- no mezclar evidencia histórica del piloto antiguo con el piloto greenfield;
- no usar un rediseño visual como sustituto de aceptación de workflow;
- no declarar product-market fit a partir de pruebas internas.

## 6. Evidencia requerida para ejecutar esta transición

- repo430 + SHA y closure commit;
- `git fetch` y ahead/behind reproducibles;
- branch limpio antes del push;
- owner approval de esta decisión;
- successor/rebaseline documentado antes de mutaciones posteriores.

## 7. Comandos de verificación recomendados

```text
git status -sb
git fetch origin
git rev-list --left-right --count origin/official/devpilot-local...official/devpilot-local
git rev-parse HEAD
git diff --quiet && git diff --cached --quiet
```

## 8. Adjudicación owner

**APPROVED.** Se acepta que repo430 es immutable closure authority, que el remoto debe ponerse al día por fast-forward y que el siguiente producto se valida primero con un piloto greenfield separado del piloto legacy.

**BLOCK operativo:** reescribir repo430, forzar Git remoto o ejecutar un piloto sin una autoridad successor clara sigue prohibido.
