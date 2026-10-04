---
doc_id: "ADR-DEVPL-GSDLC-13-D-04-GREENFIELD-FIRST-STORY-GIT-BASELINE-RECONCILIATION"
title: "13-D-04 — Reconciliación del baseline Git en el primer commit greenfield"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-10-04"
approval: "projected-for-owner-windows-validation"
---

# ADR — Reconciliación del baseline Git en el primer commit greenfield

## Contexto

El contrato histórico de GSDLC-10-D exige que el dirty set de Git coincida exactamente con el `SourceChangePlan` de la Story antes de construir `CommitPlan`. Esa invariante es correcta para Stories posteriores sobre un baseline Git ya reconciliado.

El Pilot A greenfield llega por primera vez al checkpoint Git después de haber producido mediante flujos gobernados de 13-C los artefactos FROZEN de Vision, Scope, Requirements, Architecture, ADRs, Security, Test Strategy y Traceability. El workspace conserva esos documentos como project source no trackeado porque hasta 13-D-04 no existió un checkpoint de commit. Además, `outputs/**` contiene runtime/evidence local y no está ignorado por el `.gitignore` histórico del proyecto.

Por tanto, aplicar literalmente `dirty == SourceChangePlan.exact_path_allowlist` bloquearía el primer commit aunque la Story D02/D03 sea correcta. Usar `git add .`, borrar outputs o efectuar un commit manual de baseline rompería el contrato de autoridad del piloto.

## Decisión

D04 conserva un único motor Git y amplía únicamente la construcción/revalidación del **primer CommitPlan greenfield** con una reconciliación bounded:

1. Los paths del `SourceChangePlan` continúan siendo obligatorios y se validan contra sus postimages aprobados.
2. `outputs/**` se clasifica como runtime/evidence, permanece físicamente disponible y se excluye del inventario de **source dirty paths** de Story Git. Nunca se stagea ni se incorpora al commit de la Story.
3. Un dirty path adicional solo puede incorporarse al primer CommitPlan si:
   - todavía está `untracked`;
   - pertenece a un stage definido por el catálogo Pre-code y ese stage está `FROZEN` en el runtime server-authoritative del mismo workspace;
   - el contenido actual coincide semánticamente con `approved_sha256`; o
   - es un ADR standalone de Architecture incluido en el receipt atómico `devpilot.gsdlc13c02.architecture_adr_bundle_execution.v1`, cuyo approval persistido sigue `APPROVED`, enlaza el mismo plan/hash/workspace/path set y cuyo SHA coincide con el archivo actual.
4. Cualquier otro dirty path continúa en `BLOCK`.
5. Un artefacto Pre-code ya trackeado pero modificado **no** puede absorberse como baseline; queda `BLOCK`. La excepción es first-commit-only.
6. `CommitPlan.files[].change_operation` distingue `GREENFIELD_BASELINE_PRECODE` y `GREENFIELD_BASELINE_ADR` de los cambios de Story.
7. Stage continúa exact-path, approval-bound y con `git add .=false`.
8. Stage approval y commit approval siguen siendo decisiones humanas separadas.
9. Commit continúa sin push, force, rebase, reset-hard ni shell.
10. Tras commit, la limpieza contractual se evalúa sobre **source Git**; `outputs/**` puede seguir untracked como runtime state sin invalidar el GitCommitRecord.
11. El bootstrap de proyectos futuros añade `outputs/` al `.gitignore`, de modo que esta deuda no se replique.

## Alternativas descartadas

### Commit manual previo del baseline

Descartado: introduciría una mutación Git fuera de la capability gobernada y fuera del Run Card D04.

### `git add .`

Descartado: podría incluir runtime/evidence y cualquier drift desconocido; viola explícitamente Sprint/Runbook.

### Borrar `outputs/`

Descartado: destruye evidencia y estado de resumability.

### Ignorar todo `docs/**`

Descartado: los documentos 13-C son project source aprobado y deben quedar versionados.

### Permitir cualquier untracked file en el primer commit

Descartado: transformaría la reconciliación en bypass de la allowlist.

## Consecuencias

### Positivas

- El primer commit greenfield puede incluir de forma trazable el baseline técnico/documental ya aprobado y el delta exacto de RF-001.
- Runtime evidence queda fuera de source Git sin destruirse.
- El comportamiento de Stories posteriores vuelve naturalmente al modelo normal: dirty source = SourceChangePlan.
- Se preservan las dos approvals Git y los no-go históricos.

### Riesgos y límites

- Esta reconciliación es deliberadamente específica al primer baseline greenfield y a autoridades Pre-code ya existentes; no es un importador genérico de archivos.
- `worktree_clean=true` en el GitCommitRecord significa source/index gobernado limpio; puede seguir existiendo runtime-only `outputs/**` no trackeado en el proyecto histórico.
- Release Readiness deberá conservar esta misma separación source/runtime o reconciliar el `.gitignore` mediante un flujo gobernado posterior; D04 no amplía D07.

## PASS/BLOCK

PASS si el CommitPlan contiene únicamente `Story exact paths + authority-verified first-greenfield baseline`, excluye `outputs/**`, las dos approvals son independientes y el commit exacto deja Story `DONE` sin push.

BLOCK ante baseline no FROZEN, hash drift, receipt/approval ADR no enlazado, path adicional desconocido, baseline path ya trackeado con drift, staged set previo, Quality stale o cualquier operación Git destructiva/no autorizada.

## Verificación

```text
python -m pytest -q -p no:cacheprovider tests/test_devpl_gsdlc_10_d_story_git_commit.py tests/test_workspace_git_operations_service.py tests/test_api_workspace_git_operations.py tests/test_devpl_gsdlc_10_e_story_cycle_lifecycle.py
python -m devpilot_core docs-governance validate --json
```

Full Regression en 13-D-04: `0`.
