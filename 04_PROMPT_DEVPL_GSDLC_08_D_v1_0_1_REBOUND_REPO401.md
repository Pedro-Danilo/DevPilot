---
doc_id: "04_PROMPT_DEVPL_GSDLC_08_D_V1_0_1_REBOUND_REPO401"
title: "DEVPL-GSDLC-08-D — Sprint planning capacity and dependencies"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "approved_by_owner"
source_policy: "repo401/current-windows-validated-successor-of-DEVPL-GSDLC-08-C"
full_regression_runs: 0
browser_required: "focal-if-SprintPlanner-UI-changed"
---

## 0. Rebind de autoridad de ejecución — repo401

Para esta ejecución de `DEVPL-GSDLC-08-D`, la fuente técnica current-active es exclusivamente:

- repo: `repo_DevPilot_Local_401_DEVPL_GSDLC_08_C_BACKLOG_DERIVATION_PRIORITIZATION_WINDOWS_VALIDATED_CANDIDATE.zip`;
- commit: `5adbfc995f02eb0210ce3300487789e639972c59`;
- SHA-256: `6dc2f27659167ef549506d563c50f6666cb2e4335cfc4de9f25f0bb12f02c9aa`;
- `GSDLC-08-C = CLOSED/PASS/WINDOWS-VALIDATED`;
- `GSDLC-08-D = AUTHORIZED/PENDING-IMPLEMENTATION`.

Las referencias a repo397 en las reglas transversales se conservan únicamente como autoridad inicial histórica de la ola; no autorizan retroceso de ejecución. D se implementa sobre repo401 o un successor Windows-validado explícito.

# DEVPL-GSDLC-08-D — Sprint planning, capacity and dependencies

## 1. Misión

Construir `SprintPlanner` y `SprintPlan` para convertir stories READY en sprints ejecutables, respetando capacidad, prerequisite/dependency order, Definition of Ready/Done, test intent, risk focus y approval/freeze.

## 2. Diseño

- capacity explícita, unidades documentadas y warnings de overcommit;
- prerequisite graph validado antes de scheduling;
- blocked story nunca entra silenciosamente;
- DoR/DoD y test intent versionados;
- owner/product-owner approval role-bound;
- freeze con revision/hash;
- no runtime/coding action;
- ningún scheduler planning debe ejecutar source/code.

## 3. Pruebas

- dependency violation;
- capacity warning/overcommit;
- blocked story scheduling;
- invalid readiness;
- approval/freeze role tests;
- Test Impact + acumulativa A→D;
- focal browser si cambia SprintPlanner UI;
- Contract/Documentation impact y historical sweep.

No full.

## 4. Pre-full readiness para E

D debe producir un handoff machine-readable que permita a E saber:

- changed paths acumulados A→D;
- tests nuevos;
- TCR/source registry sync;
- browser surfaces pendientes de closure;
- S0/S1;
- Contract Reconciliation Sweep inputs;
- full budget sigue `0/1`;
- parallel mode sigue `AVAILABLE-NOT-DEFAULT` salvo owner adjudication explícita posterior.

## 5. PASS

- sprint ordenado y ejecutable;
- selected stories READY;
- dependency/capacity blockers visibles;
- approval válido;
- full=0.

## 6. Salida

Autoriza 08-E únicamente después de Windows PASS.

Commit sugerido:
`feat(gsdlc-08): add governed sprint planning and capacity validation`


## Reglas transversales obligatorias

- Ingeniería acumulativa: no retroceder a baselines históricos. La autoridad inicial de la ola es `repo_DevPilot_Local_397_FRX_V2_3_E_ONE_FULL_SAFE_PARALLEL_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip` / `ba1a87adf7d7b17a2f41f1c5821b86a86b762877` / SHA-256 `109045dccb59fe235c60aac688dcee17e169dae174428df04fb3e1925dbff72a`; cada micro-sprint posterior usa únicamente el successor Windows-validado del anterior.
- No full regression por rutina fuera de `DEVPL-GSDLC-08-E`.
- Test Impact + pruebas focales + acumulativas + validators determinísticos en A-D.
- Antes de cada cierre: `historical_contract_sweep` y `documentation/contract impact`.
- Antes de la única full E: `Contract Reconciliation Sweep` duro, S0/S1=0, Project State/Source Registry/README/roadmap coherentes.
- Los tests nuevos se incorporan a la colección global automáticamente. Todo nodeid nuevo entra al isolation registry como `UNCLASSIFIED` y `parallel_safe=false`; no se promueve por nombre, duración o un PASS aislado.
- La full E usa por defecto scheduler temporal/coarsened serial (`workers=1`) porque v2.3 terminó `PASS/AVAILABLE-NOT-DEFAULT`. Safe parallel `workers<=2` solo puede usarse si el owner lo autoriza explícitamente antes de iniciar la única full y existe feasibility/isolation evidence vigente.
- Una full interrumpida se reanuda dentro de la misma logical session y ejecuta solo `UNEXECUTED`.
- Una full con FAIL funcional no se repite. Recovery: exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard + composite adjudication.
- No `git reset --hard`, `git clean`, force-push, borrado de `.git`, ni limpieza destructiva de survivors.
- Toda comparación de source debe ser Git-semántica; diferencias puramente LF/CRLF son advisory y nunca causa de BLOCK.
- Operador Windows reentrante/resumible, con receipts sticky. Reducir comprobaciones redundantes y no depender de semántica accidental de PowerShell.
- Scripts de operador preferentemente Python. PowerShell solo como comandos de una línea con PASS verde / BLOCK rojo.
- API/UI nunca background. Si un micro-sprint necesita runtime browser, usar exactamente tres consolas: 1 operador/comandos, 2 API foreground, 3 UI foreground. Si no requiere browser, no levantar API/UI.
- Runtime stores (`auth.db*`, `devpilot.db*` y equivalentes) son `runtime-ephemeral`; no copiarlos a fixtures, candidates ni ZIPs.
- Local/mock primero. Ninguna API externa ni costo son requisito de aceptación salvo que el backlog lo declare expresamente.

