---
doc_id: "DEVPL-GSDLC-13-D-04-GREENFIELD-GIT-BASELINE-ADJUDICATION"
title: "13-D-04 — Adjudicación del baseline Git del primer Story commit greenfield"
status: "reviewed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-10-04"
approval: "projected-for-owner-windows-validation"
---

# 13-D-04 — Adjudicación del baseline Git greenfield

## Hallazgo

El pre-audit de D04 sobre la fuente Windows sucesora de D03 confirmó que GSDLC-10-D aislado está sano, pero el Pilot A no satisface su precondición histórica `dirty paths == SourceChangePlan exact paths`.

El snapshot real del workspace muestra como untracked:

- siete artefactos principales Pre-code ya FROZEN;
- cuatro ADR standalone approval-bound;
- `outputs/**` runtime/evidence acumulados desde Planning/Story execution;
- los cuatro paths de implementación/test de `story-rf-001`.

El `SourceChangePlan` de RF-001 contiene únicamente los cuatro paths de implementación/test. Por tanto, la capability histórica bloquearía antes de `CommitPlan` con `GSDLC10D_UNEXPECTED_DIRTY_PATH_BLOCK`.

Este riesgo ya había sido identificado por la auditoría D02 del Pilot A: el único commit del workspace era el bootstrap inicial, `docs/** + outputs/**` seguían untracked y `.gitignore` no contenía `outputs/`. D02 ordenó carry-forward y prohibió resolverlo con terminal manual.

## RCA

No es un fallo del exact-stage engine. Es una integración tardía entre dos contratos correctos de forma aislada:

1. 13-C permitió que source documental aprobado se materializara antes del primer checkpoint Git del piloto.
2. GSDLC-10-D fue diseñado para una Story sobre un baseline Git ya limpio/reconciliado.
3. El bootstrap greenfield histórico no ignoró `outputs/`.

## Corrective autorizado

Se adopta la decisión de `ADR-DEVPL-GSDLC-13-D-04-GREENFIELD-FIRST-STORY-GIT-BASELINE-RECONCILIATION`:

- `outputs/**` queda fuera de source Git authority;
- artefactos Pre-code adicionales solo entran al primer CommitPlan si runtime FROZEN + hash exacto los acredita;
- ADRs requieren receipt + approval persistido y exact binding;
- solo untracked baseline puede absorberse;
- todo path desconocido sigue fail-closed;
- futuros bootstraps ignoran `outputs/` por defecto.

## No-go preservados

- no `git add .`;
- no push/force-push;
- no rebase;
- no reset-hard;
- no operador escribiendo source/project para “preparar” el commit;
- no borrado de outputs;
- no Full Regression;
- no combinación de stage approval y commit approval.

## Evidencia local

La línea focal ampliada después del corrective debe incluir los tests históricos de GSDLC-10-D y los nuevos casos first-greenfield:

- baseline FROZEN/ADR approval-bound incluido;
- runtime outputs excluidos;
- baseline drift bloqueado;
- tracked baseline drift bloqueado;
- path desconocido sigue bloqueado;
- bootstrap futuro incluye `outputs/` en `.gitignore`.

## PASS/BLOCK para Windows

PASS solo después de que el Owner observe en UI un CommitPlan que diferencie los cuatro Story paths del baseline greenfield verificado, ejecute dos approvals distintas, stage exacto, commit exacto, GitCommitRecord, Story `DONE`, Project Status siguiente acción y `push=false`.

BLOCK si DevPilot necesita terminal para mutar el proyecto, si aparece un path no acreditado, si se stagea `outputs/`, si las approvals son la misma decisión o si Full Regression > 0.
