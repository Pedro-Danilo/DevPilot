---
doc_id: "DEVPL-UOC-005-CLOSURE-REPORT"
title: "UOC-005 — Closure report"
status: "implemented-initial"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-08-09"
approval: "pending_windows_browser_git_closure"
---

# UOC-005 — Closure report

## Estado

**NO CERRADO todavía.** La implementación candidata está disponible sobre el baseline UOC-004 repo 332, pero el cierre requiere ejecutar en Windows los gates focales/globales impactados, browser acceptance con apply/rollback real sobre fixture controlado, source commit, fast-forward canónico, reconciliación final y baseline repo 333.

UOC-006 permanece **NO autorizado** hasta que este documento sea promovido a `status: approved`, `version: 1.0.0` y la evidencia autoritativa registre `CLOSED/PASS`.

## Base

- Baseline: `repo_DevPilot_Local_332_POST_H_EVAL_002_UOC_004.zip`.
- Closure commit base: `12334ffa5ea181f7d72fd66e55fb383baed2195f`.
- Rama canónica: `eval/post-h-eval-002-02-a-onboarding`.
- Rama fuente propuesta: `feat/post-h-eval-002-uoc-005-approval-apply-rollback`.

## Criterios obligatorios

### PASS

- focused implementation tests PASS;
- cumulative UOC-001→UOC-005 contracts PASS;
- schema/API/UI/TCR/Project State/Docs Governance PASS;
- TypeScript/Vite/smokes PASS;
- browser apply PASS;
- browser rollback PASS;
- negative approval/stale/expired/hash-mismatch PASS;
- zero unauthorized writes PASS;
- generic patch/apply/rollback no-go intactos;
- S0=0, S1=0;
- Git source/canonical refs sincronizadas;
- repo 333 exact-tree y limpio generado.

### BLOCK

Cualquier gate anterior faltante o fallido mantiene este sprint abierto y mantiene `uoc_006_authorized=false`.

## Evidencia requerida

La guía operativa UOC-005 especifica nombres, rutas y generación de evidencia. La evidencia final debe incluir manifest, logs, reports, browser observations/captures, before/after/rollback hashes, approval records sanitizados, control backup hash, Git identity y baseline 333 con SHA-256.

## Riesgos residuales

Esta versión es `implemented-initial`: process-local plan lifetime, rollback exclusivamente pre-commit y control evidence local. UOC-007/UOC-008 deberán industrializar job persistence/heartbeat/reconciliation; UOC-006 gobernará Git write.

## Comandos de verificación

Los comandos autoritativos están únicamente en la guía operativa entregada con UOC-005.
