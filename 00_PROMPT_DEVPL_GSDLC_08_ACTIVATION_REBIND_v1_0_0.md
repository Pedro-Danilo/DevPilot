---
doc_id: "00_PROMPT_DEVPL_GSDLC_08_ACTIVATION_REBIND_V1_0_0"
title: "DEVPL-GSDLC-08 — activation/rebind to repo397"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "approved_by_owner"
source_repo: "repo_DevPilot_Local_397_FRX_V2_3_E_ONE_FULL_SAFE_PARALLEL_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "ba1a87adf7d7b17a2f41f1c5821b86a86b762877"
source_repo_sha256: "109045dccb59fe235c60aac688dcee17e169dae174428df04fb3e1925dbff72a"
functional_mutation: false
full_regression_runs: 0
browser_required: false
---
# DEVPL-GSDLC-08 — Activation/Rebind

## 1. Misión

Materializar una transición **no funcional** desde el cierre FRX-v2.3 hacia DEVPL-GSDLC-08, incorporar al repo la owner adjudication y el backlog `v1.3.0 APPROVED_REBOUND`, y reconciliar las fuentes current-active antes de que 08-A modifique producto.

## 2. Entradas obligatorias

1. `repo_DevPilot_Local_397_FRX_V2_3_E_ONE_FULL_SAFE_PARALLEL_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip` con SHA-256 `109045dccb59fe235c60aac688dcee17e169dae174428df04fb3e1925dbff72a`.
2. Commit de cierre `ba1a87adf7d7b17a2f41f1c5821b86a86b762877`.
3. `DEVPL_FULL_REGRESSION_V2_3_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md`.
4. `DEVPL-GSDLC-08_planning_workbench_roadmap_backlog_sprints_v1_3_0_APPROVED_REBOUND.md`.
5. Evidencia de que FRX-v2.3-E cerró por composite recovery: full original `1/1`, selective `65/65 PASS`, composite `2904 PASS + 5 SKIP`, second-full=false.

## 3. Mutaciones permitidas

Solo documentación/gobernanza:

- registrar el closure adjudication v2.3 como current-active successor del backlog v1.4.0;
- incorporar el backlog GSDLC-08 v1.3.0 APPROVED_REBOUND;
- Project State: GSDLC-08 `APPROVED/ACTIVE`, current/next `08-A/08-B` según la convención vigente, source successor del activation commit;
- Source Registry y derived counters;
- README current status, roadmap canónico, changelog;
- contratos de documentación estrictamente necesarios.

No modificar `src/`, UI funcional, API, modelos de dominio ni workspace de usuario.

## 4. Drift que debe corregirse

El backlog v2.3 v1.4.0 conserva `status: approved` aunque Project State y su sección final expresan cierre. No reescribir el documento histórico: registrar el nuevo closure adjudication successor y hacer que las fuentes current-active apunten a él.

README puede conservar notas históricas fechadas que decían “GSDLC-08 deferred”, pero debe existir un estado current-active inequívoco que indique v2.3 CLOSED y 08-A autorizado.

## 5. Validación

- source ZIP SHA y hygiene;
- Git ancestry/source commit;
- Project State;
- Documentation Governance;
- TCR v1/v2;
- Evidence Freshness;
- focal de activation/rebind;
- source semantic guard final.

Full=0. Browser=0.

## 6. PASS

PASS únicamente si:

- repo397 es parent;
- v2.3 aparece CLOSED/PASS current-active sin reescribir evidencia histórica;
- backlog 08 APPROVED_REBOUND está registrado;
- 08-A queda inequívocamente autorizado;
- todos los gates anteriores pasan;
- source clean;
- no full/browser/network.

## 7. BLOCK

Cualquier intento de ejecutar contra repo341, modificar producto, reescribir la full v2.3, consumir full, dejar dos authorities current-active o producir drift documental.

## 8. Salida

Successor Windows-validado de activation/rebind, que será la única autoridad de entrada de `DEVPL-GSDLC-08-A`.

Commit sugerido:

`chore(gsdlc-08): activate approved planning workbench backlog on repo397`


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

