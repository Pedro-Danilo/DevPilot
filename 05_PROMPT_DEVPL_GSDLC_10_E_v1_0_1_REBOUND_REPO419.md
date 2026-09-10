---
doc_id: "PROMPT-DEVPL-GSDLC-10-E"
title: "DEVPL-GSDLC-10-E — End-to-end story cycle browser closure and one-full adjudication"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-09"
approval: "approved_by_owner/rebound_repo419_after_GSDLC-10-D-windows-closure"
precondition: "GSDLC-10-D CLOSED/PASS/WINDOWS-VALIDATED"
execution_source_policy: "repo_DevPilot_Local_419_DEVPL_GSDLC_10_D_RBAC_GOVERNED_STAGE_COMMIT_WINDOWS_VALIDATED_CANDIDATE.zip / e1fbc1c93eba098cf7b82272dcaa9fe9b0100149 / 9cd19db4f0a0c28e59e69cd4184e73570815596618ada9581048d21aa00e0db5"
source_repo: "repo_DevPilot_Local_419_DEVPL_GSDLC_10_D_RBAC_GOVERNED_STAGE_COMMIT_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "e1fbc1c93eba098cf7b82272dcaa9fe9b0100149"
source_repo_sha256: "9cd19db4f0a0c28e59e69cd4184e73570815596618ada9581048d21aa00e0db5"
full_regression_budget: "exactly 1 logical Full for DEVPL-GSDLC-10 unless already consumed by explicit owner-approved hard trigger"
frx_execution_profile_id: "frx-v2.4-current"
frx_execution_profile_sha256: "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"
browser_policy: "required real-browser end-to-end closure"
---

# 05 — GSDLC-10-E

Cierra GSDLC-10 demostrando una story completa `planning/context → code/change plan → Validate/TestPlan → jobs → Quality/remediation → governed commit → trace graph`, desde UI, con una única logical Full Regression al final de los gates pre-Full.

## Política transversal obligatoria

- Ingeniería acumulativa: nunca retroceder a un repo histórico para simplificar implementación.
- **Execution source:** usar el successor Windows-validado inmediatamente anterior. Para el inicio de GSDLC-10 es repo414; repo413 se conserva como baseline canónico funcional de cierre de GSDLC-09.
- No `reset --hard`, `git clean`, force push ni eliminación de `.git`.
- Operadores Windows: Python preferido, reentrantes y deliberadamente pequeños; validar solo lo necesario según Test Impact.
- Cada instrucción PowerShell de una guía Windows debe ir en una sola línea, claramente identificada como `Powershell`, y terminar en PASS verde o BLOCK rojo.
- API/UI solo cuando el micro-sprint necesite browser; cuando se requieran, exactamente tres consolas separadas y API/UI siempre foreground.
- Runtime stores (`auth.db*`, `devpilot.db*` y equivalentes), secretos, `.git`, `.venv`, caches, `outputs/` y `node_modules/` quedan fuera de fixtures/evidence/packages finales.
- LF/CRLF jamás puede causar BLOCK: comparar contenido Git o hashes semánticos UTF-8/LF, no representación física accidental.
- Historical Contract Authority y Contract Reconciliation Sweep se ejecutan de forma proporcional al impacto. No editar tests históricos solo para hacerlos pasar.
- Clasificación de contratos: `historical-freeze`, `current-active`, `successor-needed`, `deprecated-after-proof`, `derived`, `runtime-ephemeral`.
- **Drift documental puntual:** si no rompe seguridad, autoridad, trazabilidad, DoD ni la invariante funcional, se corrige dentro del micro-sprint activo/siguiente; no crear micro-sprint, operador ni repo independiente solo por ese drift.
- FRX low-level knobs (`planner`, `max_nodeids`, nodeid transport, workers directos) no pertenecen a operadores GSDLC. El `FullRegressionExecutionProfile` current-active es autoridad.
- Agentes/modelos pueden proponer; nunca obtienen por la ruta/modelo autoridad para aprobar, waivar, stage, commit o ejecutar mutaciones.


## Invariante E2E

El operador puede preparar fixture, iniciar API/UI y recolectar evidencia, pero **no puede sustituir el normal journey** escribiendo código, lanzando los tests de la story, aprobando Quality, haciendo stage o commit mediante PowerShell/CLI. Esas acciones deben ocurrir a través de DevPilot.

## Browser mínimo obligatorio

Demostrar en browser real:
1. story actual y change plan aprobado;
2. `Validar` → Test Impact/StoryTestPlan explainable;
3. plan/ejecución de jobs tipados;
4. un FAIL de prueba inyectado de forma controlada;
5. Quality BLOCK visible;
6. remediation manual o agent-assisted proposal con autoridad separada;
7. impacted retest PASS;
8. Quality PASS → COMMIT_READY;
9. CommitPlan exacto + approval/RBAC;
10. commit ejecutado por DevPilot;
11. trace graph requirement→story→files→tests→quality→commit;
12. Project Status avanza coherentemente.

Capturas: únicas, numeradas y acompañadas por verifier machine-readable. No duplicar screenshots por correctives que no cambien el journey demostrado.

## Orden irreversible antes de consumir Full

1. GSDLC-10-A→D `CLOSED/PASS/WINDOWS-VALIDATED`.
2. E2E browser acceptance PASS.
3. Story committed via governed UI journey.
4. Trace graph complete.
5. S0/S1=0.
6. Source delta manifest final.
7. Historical Contract Authority sweep PASS.
8. Contract Reconciliation Sweep PASS.
9. Project State / Source Registry / README / roadmap current-active coherentes **en aspectos que afecten closure/authority**; drift menor no bloqueante puede registrarse para el siguiente sprint.
10. runtime-ephemeral/secret exclusion PASS.
11. FRX-v2.4/current-profile preflight PASS.
12. Full budget acreditado `0/1` salvo hard-trigger previo owner-approved.
13. profile hash/version current PASS.
14. topology/isolation/duration registry prerequisites requeridos por el profile PASS.
15. projected topology/ETA/evidence path registrados.

Solo entonces iniciar la única logical Full.

## Política Full obligatoria

- El operador GSDLC-10-E invoca el `FullRegressionExecutionProfile` por ID/current authority; no pasa planner/max_nodeids/workers/nodeid transport directos.
- No cambiar collection/profile/plan durante la logical session.
- Si hay interrupción de infraestructura, reanudar **misma session** y solo `UNEXECUTED`.
- Si termina FAIL/ERROR funcional: preservar Full original inmutable y **NO RERUN**.

### Recovery funcional autorizado

1. exact failed/error nodeid retest;
2. bounded impacted retest derivado de Test Impact;
3. Historical Regression Guard;
4. post-recovery deterministic gates;
5. composite adjudication con accounting 100%;
6. 0 FAIL/ERROR terminal en el recovery set;
7. no segunda Full.

La Full histórica FAIL no se reescribe como PASS; el backlog puede cerrar por `PASS/COMPOSITE-FULL-PLUS-SELECTIVE-RECOVERY` cuando toda la evidencia lo justifique.

## Evidencia mínima

- story_cycle_e2e_report;
- screenshots + browser verifier;
- StoryTestPlan/TestImpact report;
- job results/log refs/JUnit;
- Quality Report + remediation trace;
- CommitPlan + GitCommitRecord/hash;
- trace graph;
- source delta;
- HCA/Contract Reconciliation;
- Full session marker/log/JUnit/accounting o composite recovery;
- Git pre/post identity;
- S0/S1 list;
- hashes de packages/evidence;
- `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## Entregables obligatorios de implementación/Windows

Al terminar este micro-sprint, entregar únicamente artefactos coherentes entre sí:

- source delta manifest exacto;
- implementation report con capacidades, archivos creados/modificados, riesgos y limitaciones;
- Test Impact + focal/acumulativa y gates que correspondan al delta;
- historical contract sweep / Contract Reconciliation proporcional;
- Windows validation bundle con operador Python pequeño y reentrante;
- guía única `.md` para Windows, orientada a personal beginner-medio; comandos PowerShell de una sola línea, identificados como `Powershell`, PASS verde/BLOCK rojo;
- evidencia machine-readable y manual/browser solo cuando aplique;
- después de PASS Windows: repo ZIP limpio + components ZIP + SHA-256 + packaging result;
- identidad Git pre/post y commit sugerido/real.

El operador no debe instalar dependencias ad hoc, no debe ejecutar checks ajenos al delta solo “por seguridad”, y debe reconocer/reutilizar estados PASS previos cuya evidencia esté hash-bound e íntegra.

## PASS

- one complete story UI-native;
- no operator substitute writes/tests/commit;
- governed exact commit;
- traceability complete;
- Full/composite 100% accounted;
- no second Full;
- S0/S1=0.

Salida: `GSDLC-10-E = CLOSED/PASS`, `DEVPL-GSDLC-10 = CLOSED/PASS`; autoriza GSDLC-11 únicamente después de la adjudicación final.

## 10-E corrective de continuidad de contexto project-scoped — 2026-09-10

La autoridad de proyecto no depende de `sessionStorage`. Para rutas `scope=project`, si falta el contexto UX, la UI debe recuperar de forma read-only usando el único `workspace_scope` de la sesión humana autenticada y validar el mismo workspace mediante Project Status server-side. Scope ausente/ambiguo o recovery inválido debe fallar cerrado. Este corrective no sustituye Crear/Abrir/Importar para una sesión sin proyecto activo y no concede RBAC adicional.
