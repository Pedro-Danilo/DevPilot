---
doc_id: "03_PROMPT_DEVPL_GSDLC_08_C_V1_0_1_REBOUND_REPO400"
title: "DEVPL-GSDLC-08-C — Backlog derivation and prioritization"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-04"
approval: "approved_by_owner/rebound_repo400"
source_policy: "successor-of-DEVPL-GSDLC-08-B/windows-validated"
source_repo: "repo_DevPilot_Local_400_DEVPL_GSDLC_08_B_ROADMAP_WORKBENCH_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "0533d7427181fd3e3e39635d136540f1f127c3e3"
source_repo_sha256: "4250aa0a7ff0208e27e48b74af2d117a0cfa5c98363810694d54885ec2aed6ad"
full_regression_runs: 0
browser_required: false
---
# DEVPL-GSDLC-08-C — Backlog derivation and prioritization

## 1. Misión

Derivar o crear epics/stories desde roadmap y requirements, con acceptance criteria, requirements/ADR/risk/test-intent links, priority/value/risk rationale y cobertura explicable.

## 2. Autoridad de ejecución

Este successor sustituye el binding histórico del prompt v1.0.0 para esta ejecución. La única autoridad inicial es repo400 / commit `0533d7427181fd3e3e39635d136540f1f127c3e3` / SHA-256 `4250aa0a7ff0208e27e48b74af2d117a0cfa5c98363810694d54885ec2aed6ad`.

GSDLC-08-B está `CLOSED/PASS/WINDOWS-VALIDATED` y fue ratificado mediante suplemento browser independiente sin mutación de source/Git y con `full=0`.

## 3. Reglas funcionales

- `BacklogWorkbench` y `RequirementCoverageService`;
- required traceability 100% o blocker explícito;
- detectar orphan requirements, duplicated stories y dependency gaps;
- priority no puede ser un número opaco: conservar rationale/source;
- manual edits prevalecen y quedan auditables;
- agent suggestions son proposals, no approvals;
- review/approve/freeze role-bound.

## 4. Contratos históricos

No confundir roadmaps/backlogs del workspace con el roadmap/backlog canónico de DevPilot. Los contratos sobre `docs/00_product/product_roadmap.md` y equivalentes deben scopearse a repo DevPilot.

Clasificar cada contrato tocado: `historical-freeze`, `current-active`, `successor-needed`, `deprecated-after-proof`, distinguiendo `derived` y `runtime-ephemeral`.

## 5. Pruebas

- 100% coverage fixtures;
- orphan/duplicate/dependency negatives;
- acceptance criteria required;
- priority schema+rationale;
- RBAC/freeze;
- Test Impact + acumulativa A→C;
- browser focal solo si C introduce/cambia UI visible;
- Docs/TCR/Project State.

**No full.** Esta implementación no introduce ruta UI/browser nueva; por tanto `browser=0`.

## 6. PASS

- coverage required =100%;
- blockers unmapped=0;
- story sin acceptance criteria bloquea;
- no drift histórico/current;
- full=0;
- browser=0.

## 7. Salida

Autoriza 08-D únicamente después de Windows PASS.

Commit sugerido: `feat(gsdlc-08): add traceable backlog derivation and prioritization`

## 8. Reglas transversales obligatorias

- Ingeniería acumulativa: no retroceder a baselines históricos.
- No full regression fuera de 08-E por rutina.
- Test Impact + focal + acumulativa + validators determinísticos.
- Antes del cierre: historical contract sweep y documentation/contract impact.
- Tests nuevos: `UNCLASSIFIED/parallel_safe=false` hasta promoción explícita.
- No `git reset --hard`, `git clean`, force-push, borrado de `.git` ni limpieza destructiva.
- Comparación de source Git-semántica; LF/CRLF solo advisory.
- Operador Windows reentrante/resumible y mínimo.
- Scripts Python preferidos; PowerShell de una línea con PASS/BLOCK.
- API/UI foreground solo cuando browser sea necesario; en C no se levanta runtime browser.
- Runtime stores `auth.db*`, `devpilot.db*` y equivalentes excluidos de fixtures/candidates/ZIPs.
- Local/mock first; ninguna API externa o costo es requisito.
