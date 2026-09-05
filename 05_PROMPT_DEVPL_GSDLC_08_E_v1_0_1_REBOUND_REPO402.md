---
doc_id: "05_PROMPT_DEVPL_GSDLC_08_E_V1_0_1_REBOUND_REPO402"
title: "DEVPL-GSDLC-08-E — Planning traceability and Project Status browser closure"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "approved_by_owner"
source_policy: "successor-of-DEVPL-GSDLC-08-D/windows-validated"
source_repo: "repo_DevPilot_Local_402_DEVPL_GSDLC_08_D_SPRINT_PLANNING_CAPACITY_DEPENDENCIES_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "d852067e3f7fd2c5c77d7d9195e110a8938f02eb"
source_repo_sha256: "f7a95608d764f807350f61f8582499f00ac801d4f83046afc4da81d531fe963b"
full_regression_policy: "exactly-one-logical-full"
default_full_workers: 1
safe_parallel_default: false
safe_parallel_opt_in_max_workers: 2
browser_required: true
---
# DEVPL-GSDLC-08-E — Planning traceability and Project Status browser closure

> **Execution rebind v1.0.1.** Para esta ejecución la autoridad inicial es repo402/`d852067e…`, successor Windows-validado de 08-D. Las referencias repo397 en reglas transversales se conservan únicamente como origen de la ola; no autorizan retroceso de baseline.

## 1. Misión

Cerrar la ola Planning Workbench como comportamiento de producto: `PRE_CODE_READY → PLANNING → IMPLEMENTING_READY`, trace graph requirement→milestone→epic→story→sprint, StepActionAdvisor planning, manual/import/agent choices, approval/freeze y browser end-to-end.

## 2. Precondiciones duras antes de la full

1. A-D `CLOSED/PASS/WINDOWS-VALIDATED`.
2. Browser/capability acceptance de la superficie planning PASS.
3. Required planning coverage=100%; S0/S1=0.
4. Project State/README/Source Registry/roadmap CURRENT coherentes.
5. `historical_contract_sweep` y `contract_reconciliation_sweep` PASS.
6. Schema metadata, derived counters, capability mappings, RBAC/approval bindings y runtime-ephemeral exclusions PASS.
7. Collection actual sellada.
8. Full budget `0/1`.
9. Test duration registry/isolation registry/conflict data vigentes para la colección.

Si cualquiera falla, corregir **antes** de iniciar la full.

## 3. Browser closure

Usar exactamente tres consolas foreground. Demostrar:

- entrada desde PRE_CODE_READY;
- Construir roadmap;
- manual, import y agent-assisted como rutas visibles;
- roadmap review/approve/freeze;
- backlog derivation/coverage;
- sprint planning/capacity/dependencies;
- approval;
- trace graph;
- transición final IMPLEMENTING_READY;
- RBAC negative case;
- accesibilidad/errores críticos.

Capturas: solo estados de aceptación definidos por la guía Windows; registrar URL/rol/acción/resultado y no capturar secretos.

## 4. Única full regression

### Modo por defecto

La decisión heredada de v2.3 es `PASS/AVAILABLE-NOT-DEFAULT`, por lo que la full de 08-E debe ejecutarse por defecto con:

- Full Regression Execution v2 resumible;
- temporal duration-balanced/coarsened manifests;
- `workers=1`;
- semantic Git source guard;
- completion-first;
- live per-node receipts;
- exact accounting;
- no second full.

### Opt-in paralelo

`workers<=2` solo si **antes de full-start** el owner aprueba explícitamente una pre-full adjudication que demuestre:

- isolation registry current;
- solo `PROVEN_PARALLEL_SAFE`;
- conflict graph sin violaciones;
- feasibility actual;
- ningún test nuevo `UNCLASSIFIED` entra en paralelo.

No ejecutar una full serial y otra paralela para comparar. El modo elegido consume la única logical full.

## 5. Tests nuevos

La collection sellada de E contiene todos los tests existentes en el successor D, incluidos los nuevos de A-D. Nodeids nuevos sin evidencia de aislamiento permanecen seriales. Los tests nuevos con duración desconocida usan cold-start bounded planning y su telemetría se ingiere después de la ejecución para futuros backlogs.

## 6. Recovery si la full no queda funcionalmente PASS

- preservar marker, collection, plan, receipts, JUnit/logs y hashes;
- no volver a ejecutar la full;
- extraer exact failed/error nodeids;
- diagnosticar y corregir causa;
- exact failed-nodeid selective retest;
- bounded impacted retest definido por Test Impact;
- Historical Regression Guard;
- post-recovery Project State/Docs/TCR/Evidence Freshness;
- composite adjudication exacta.

El composite debe mantener `full_runs=1/1` y `second_full=false`.

## 7. PASS

- UI-complete planning;
- required coverage=100%;
- mandatory CLI bridge=0 para journey normal;
- S0/S1=0;
- browser PASS;
- full/composite 100% accounted con 0 FAIL/ERROR;
- source drift=0;
- no runtime leakage;
- one full only.

## 8. Cierre

Actualizar backlog 08, roadmap, Project State, README, Source Registry, changelog, evidence freshness y autorización de GSDLC-09. Packaging Git three-state y ZIP limpio.

Commit sugerido:
`close(gsdlc-08): validate planning workbench browser and one-full closure`


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

