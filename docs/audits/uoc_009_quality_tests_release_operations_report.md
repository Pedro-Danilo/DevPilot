---
doc_id: "DEVPL-UOC-009-QUALITY-TEST-RELEASE-REPORT"
title: "UOC-009 — Quality, Tests and Release Operations Report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-11"
approval: "approved_by_owner"
---

# UOC-009 — Quality, Tests and Release Operations Report

## Baseline y autoridad

La implementación parte exclusivamente de `repo_DevPilot_Local_336_POST_H_EVAL_002_UOC_008.zip`, SHA-256 `2a1e0e2501753431cc1ac8a685b4b597ac34ebf0e48dbec8d80715bb92c1a734`, closure commit UOC-008 `c454bd92f102ed4711098dc85249722ac24d022e`. No se usa ningún candidate de prompts anteriores.

## Implementación

Se añade `QualityOperationsApplicationService`, registry de perfiles, worker tipado, seis rutas API y la UI `/quality`. El registry contiene 11 perfiles operacionales que mapean a 10 capabilities runtime únicas mediante `uoc009.quality.typed-worker`. Test Impact permanece plan-only; focused/full tests se resuelven por Test Contract Registry y argv fija del worker, nunca por shell text o paths arbitrarios del navegador.

Full regression requiere approval, budget y confirmación literal `RUN FULL REGRESSION`. Nunca se encadena automáticamente después de focused tests. Evidence packaging incluye resultados UOC-009/JUnit y contratos baseline con hashes por entrada, sin incorporar secretos ni state operativo prohibido.

## Failure replay

La primera versión preserva evidencia previa creando un nuevo plan con una nueva idempotency key. No sobrescribe el resultado anterior ni falsea su adjudicación. El clonado/replay one-click del plan anterior no se habilita todavía y queda como evolución posterior; el retry genérico UOC-008 no se usa para sortear el contrato de la operación.

## Reconciliación histórica

Se corrigieron tres congelamientos heredados sin relajar no-go gates: UOC-007/UOC-008 ya no exigen que el registry global mantenga cero adapters para siempre y congelan ese hecho en sus manifests históricos; el contrato API admite exclusivamente los envelopes POST tipados de UOC-009; el schema registry incorpora los cuatro schemas nuevos. El manifest UOC-008 también deja de declarar browser/repo336 pendientes una vez que su evidencia final los cerró.

## Validación controlada antes de Windows

- focal/API/schema: `68/68 PASS`; historical POST-H-EVAL-002 sweep: `150/150 PASS`;
- smoke adicional del service/worker después del fix de metadata: 15/15 PASS y ejecución real del worker `project-state` hasta estado terminal `pass`;
- TCR v1: PASS, 261 contracts;
- TCR v2: PASS, 261 contracts, 2 `needs-review` preexistentes;
- Project State: PASS;
- Documentation Governance: PASS, 663 docs, 0 warnings, 0 blocking drift;
- UI smoke/visual/operator-flow/route-enforcement: PASS, visual 8/8;
- Test Impact final: 55 changed paths, 149 matched contracts, 224 recommended tests, 0 unmatched, residual risk HIGH y `full_regression_required=true`;
- `git diff --check`: PASS bajo semántica Windows `core.autocrlf=true`.

`npm build` no se adjudica en el sandbox limpio porque el baseline autoritativo excluye `node_modules` y Vite no está instalado. El gate es obligatorio en Windows.

## Estrategia de regresión Windows

No se declara full regression PASS por reutilización. El operador ejecuta todos los tests impactados de Test Impact en batches reanudables. Una vez todos estén PASS y no existan unmatched paths, un waiver temporal, owner-approved y explícito permite que `HistoricalRegressionGuard` acepte no repetir el costoso `pytest -q` completo. El waiver no cubre tests fallidos, unmatched paths, S0/S1 ni browser acceptance y conserva la cadena autoritativa UOC-008 como baseline.

## Riesgos residuales y carácter preliminar

La implementación es `implemented-initial`: worker local por proceso, persistencia runtime JSON y concurrency local; UOC-008 aporta heartbeat/cancelación/orphan reconciliation. El replay de fallo se hace por nuevo plan y no por clone one-click. UOC-011 deberá endurecer retención, performance/accessibility, resiliencia prolongada y operación multi-operator.

## Cierre

El source candidate no autoriza UOC-010. Solo evidencia Windows con todos los tests impactados PASS, regression guard/waiver válido, npm build, browser acceptance, closure gates y repo337 limpio puede cambiar UOC-009 a `closed/PASS` y autorizar UOC-010.

## Correctivo C6 browser approval binding — v1.0.4

La aceptación browser detectó un defecto real de integración en `/quality`: el UI enviaba `scope=operation=quality-gate`, mientras `ApprovalService` exige que un scope explícito sea un objeto JSON serializado. El backend respondió correctamente `403 BLOCK` con `APPROVAL_SCOPE_JSON_INVALID`; el token seguía siendo válido, como demuestran los GET protegidos `200` en la misma sesión. El correctivo serializa un scope tipado `{operation_id, workspace_id, source}` y limita la mejora del mensaje 403 a `QualityOperationsView`, preservando el contrato histórico del cliente API compartido. Browser acceptance debe repetirse desde la primera captura sobre el source corregido; no se reutilizan capturas pre-patch.


## Cierre autoritativo

**CLOSED/PASS** sobre `e6b2cf8a3b2a5b308431e87b4176d95afb718ec0`. Test Impact 0 unmatched, todos los tests seleccionados PASS, browser/evidence packaging PASS y waiver temporal HistoricalRegressionGuard. Baseline `repo_DevPilot_Local_337_POST_H_EVAL_002_UOC_009.zip`; UOC-010 autorizado. La capacidad conserva madurez `implemented-initial`.
