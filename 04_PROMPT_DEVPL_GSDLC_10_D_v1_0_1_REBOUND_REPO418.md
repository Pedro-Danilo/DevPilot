---
doc_id: "PROMPT-DEVPL-GSDLC-10-D"
title: "DEVPL-GSDLC-10-D — RBAC-governed stage and commit with traceability"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-09"
approval: "approved_by_owner/rebound_repo418_after_GSDLC-10-C-windows-closure"
precondition: "GSDLC-10-C CLOSED/PASS/WINDOWS-VALIDATED and story COMMIT_READY"
execution_source_policy: "repo_DevPilot_Local_418_DEVPL_GSDLC_10_C_QUALITY_GATE_REMEDIATION_WINDOWS_VALIDATED_CANDIDATE.zip / 2ebb692ecb58f77846ac3a01b0960c9e683b506e / 82bc7e90b729c84823a1ddf5e55139016bfd3baa37e23cc4969f56d39cf38527"
source_repo: "repo_DevPilot_Local_418_DEVPL_GSDLC_10_C_QUALITY_GATE_REMEDIATION_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "2ebb692ecb58f77846ac3a01b0960c9e683b506e"
source_repo_sha256: "82bc7e90b729c84823a1ddf5e55139016bfd3baa37e23cc4969f56d39cf38527"
full_regression_runs_allowed: 0
browser_policy: "required because the governed stage/commit normal journey must be demonstrated"
---

# 04 — GSDLC-10-D

Implementa cierre de story mediante stage/commit exactos y gobernados desde UI. Reutiliza `workspace_git_operations_service.py`, `WorkspaceGitOperationsPanel.ts` y el framework de ToolIntent/ToolExecutionDecision; no crear un segundo Git engine.

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


## Contrato crítico de autoridad

- `Quality PASS + COMMIT_READY` es precondición, no autoridad suficiente por sí sola.
- DevPilot genera `CommitPlan` exacto; RBAC/policy/approval server-side determina si puede ejecutarse.
- Un agente puede sugerir mensaje/plan, nunca conceder permiso Git.
- **No push** como parte del normal journey de este sprint.
- Prohibidos force push, rebase, reset-hard y staging implícito de paths no aprobados.

## Implementación requerida

1. `CommitPlan` immutable/hash-bound con:
   - story/change-plan/quality-report IDs+hashes;
   - exact paths y expected Git status;
   - include/exclude explicit;
   - approval role/policy;
   - proposed/editable commit message;
   - trace/evidence IDs.
2. Revalidar preconditions justo antes de stage:
   - Quality Report current/no stale;
   - expected path set;
   - no unexpected dirty path;
   - preimage/current hashes cuando aplique;
   - authorized role/session.
3. Stage **exact paths**; jamás `git add .` o equivalente amplio.
4. Commit mediante typed governed operation y registrar `GitCommitRecord` con hash real, author/session, message, paths y trace links.
5. Verificar worktree del fixture/proyecto de prueba limpio después del commit y que commit contiene exactamente el delta aprobado.
6. Evidence graph binding requirement→story→change-plan→tests→quality→commit.
7. Operador Windows no puede “ayudar” ejecutando stage/commit de la story por PowerShell. La acción debe ser ejecutada por DevPilot bajo prueba.
8. Para browser/Windows usar workspace Git aislado/fixture controlado; no probar mutaciones destructivas sobre el repo oficial de DevPilot.
9. Drift documental menor se absorbe aquí.

## Pruebas

- exact staging;
- unexpected dirty path BLOCK;
- wrong role BLOCK;
- stale quality BLOCK;
- agent/model route no confiere commit authority;
- message/identity record;
- exact commit tree/path set;
- traceability payload;
- UI plan→approve→commit;
- negative destructive Git operations remain unavailable.

## Regresión

**Full = 0.** Focal + Test Impact + acumulativa A→D + Git historical guard/gates proporcionales.

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

- commit exact approved delta;
- repo/fixture limpio;
- RBAC/approval acreditados;
- no unapproved file staged;
- traceability complete;
- S0/S1=0.

Salida: autoriza GSDLC-10-E.
