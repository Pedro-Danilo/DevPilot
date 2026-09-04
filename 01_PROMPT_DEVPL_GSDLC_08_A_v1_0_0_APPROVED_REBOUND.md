---
doc_id: "01_PROMPT_DEVPL_GSDLC_08_A_V1_0_0_APPROVED_REBOUND"
title: "DEVPL-GSDLC-08-A — Planning domain schemas and lifecycle"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "approved_by_owner"
source_policy: "successor-of-DEVPL-GSDLC-08-ACTIVATION/windows-validated"
full_regression_runs: 0
browser_required: false
---
# DEVPL-GSDLC-08-A — Planning domain schemas and lifecycle

## 1. Misión

Implementar el dominio planning antes de cualquier generación de roadmap: `Milestone`, `Epic`, `Story`, `Sprint`, `Dependency` y `PlanningState`, con IDs estables, versionado, lifecycle, ownership, trazabilidad y dependency graph con cycle detection.

## 2. Precondiciones

- activation/rebind GSDLC-08 CLOSED/PASS;
- GSDLC-08 v1.3.0 APPROVED_REBOUND es la autoridad;
- `PRE_CODE_READY` y proyecto activo/server-validado continúan siendo precondiciones del journey;
- no S0/S1 heredados.

## 3. Diseño obligatorio

- schemas JSON versionados y catalogados;
- aggregate/domain model separado de DTO/UI;
- IDs estables y validación de colisiones;
- PlanningState con transiciones explícitas y no implícitas;
- trace links typed hacia requirements, risks, ADRs y test intent;
- dependency graph determinístico con cycle detection y orphan detection;
- approval/freeze semantics role-bound;
- agente no puede auto-aprobar ni saltar lifecycle;
- ninguna operación planning escribe source code.

Mantener manual/local-first como ruta de primera clase.

## 4. Entregables mínimos

- schemas planning;
- servicio/modelo `PlanningState`;
- dependency graph service;
- planning contract report machine-readable;
- TCR v1/v2 y Source Registry;
- ADR si se introduce una nueva decisión transversal de lifecycle/ownership;
- tests negativos: duplicate ID, cycle, orphan trace, illegal transition, unauthorized freeze.

## 5. Pruebas

Focales del dominio + schema + negativos + Project State/Docs/TCR. Ejecutar Test Impact y acumulativa de GSDLC-08-A. `historical_contract_sweep` obligatorio.

No full. No browser salvo que se cambie accidentalmente UI, lo cual debe justificarse o posponerse.

## 6. PASS

- entidades versionables y trazables;
- graph válido;
- cycle/orphan/ID collision bloquean;
- approval/freeze no bypassable;
- 100% de tests nuevos registrados;
- full=0.

## 7. Salida

Autoriza 08-B únicamente después de Windows PASS y promoción Git gobernada.

Commit sugerido:
`feat(gsdlc-08): add planning domain lifecycle and dependency contracts`


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

