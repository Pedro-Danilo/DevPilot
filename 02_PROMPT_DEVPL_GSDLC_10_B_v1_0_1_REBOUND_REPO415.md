---
doc_id: "PROMPT-DEVPL-GSDLC-10-B"
title: "DEVPL-GSDLC-10-B — Governed test/build/lint jobs and live logs"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-09"
approval: "approved_by_owner/rebound_repo415"
precondition: "GSDLC-10-A CLOSED/PASS/WINDOWS-VALIDATED"
execution_source_policy: "immediate Windows-validated successor of GSDLC-10-A"
full_regression_runs_allowed: 0
browser_policy: "required for lifecycle/live-log UX introduced or materially changed"
base_authority_repo: "repo_DevPilot_Local_415_DEVPL_GSDLC_10_A_TEST_IMPACT_STORY_TEST_PLAN_WINDOWS_VALIDATED_CANDIDATE.zip"
base_authority_commit: "ca3fadb3febf12fa5b405712d5611bbd96d7905f"
base_authority_sha256: "39e83d8d55434f3201597cac41196c862d241bc1219a2b05d24be3000c5cd910"
frx_execution_profile_id: "frx-v2.4-current"
documentation_drift_policy: "bounded non-critical drift absorbed; no standalone corrective"

---

# 02 — GSDLC-10-B

Implementa la ejecución de los tests/build/lint elegidos por `StoryTestPlan` como **jobs tipados gobernados**, con lifecycle observable y logs seguros. Reutiliza `governed_jobs`, Job Console y Quality Operations existentes antes de crear nuevas abstracciones.

## Política transversal obligatoria

- Ingeniería acumulativa: nunca retroceder a un repo histórico para simplificar implementación.
- **Execution source:** usar el successor Windows-validado inmediatamente anterior. Para GSDLC-10-B la execution source obligatoria es repo415; repo414/repo413 quedan como hechos históricos del predecessor.
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


## Superficies a inspeccionar/reutilizar

- `src/devpilot_core/application/governed_jobs.py`;
- `governed_job_operations.py` y capability registry;
- `workspace_validation_service.py` / validation service;
- routers `jobs.py`, `quality.py`, `workspace_validations.py`;
- `ui/web/src/pages/JobsView.ts`;
- `QualityOperationsView.ts`;
- lifecycle/cancel/retry/orphan behavior ya existente.

## Implementación requerida

1. Vincular `StoryTestPlan` aprobado a uno o más `StoryValidationJob` tipados; no aceptar command strings arbitrarios.
2. Capability/command allowlist declarativa para `test`, `build`, `lint` según contrato del proyecto.
3. Lifecycle mínimo reproducible: `PLANNED → APPROVED/QUEUED → RUNNING → PASS|FAIL|ERROR|CANCELLED|TIMED_OUT`, con retry controlado donde aplique.
4. Capturar resultado estructurado y refs a JUnit/artifacts.
5. Logs:
   - bounded/paginados;
   - redactar secretos;
   - preservar stdout/stderr útil;
   - no exponer tokens/env sensibles.
6. Timeout/resource ceiling y cancelación de process tree, no solo proceso padre.
7. Reconciliar orphan job después de restart sin marcar PASS por ausencia de proceso.
8. Retry no puede cambiar plan/test set silenciosamente; crear nueva attempt identity enlazada al job original.
9. UI live/near-live: estado, heartbeat, timestamps, counters, logs y acciones permitidas.
10. Drift documental menor se absorbe aquí mismo.

## Pruebas

- lifecycle matrix;
- cancel process tree;
- timeout;
- retry identity;
- forbidden command/shell injection;
- log redaction;
- JUnit/artifact refs;
- orphan recovery;
- stale StoryTestPlan rejected;
- UI status/log/cancel/retry;
- bounded cumulative tests de 10-A y jobs/quality históricos impactados.

## Browser

Si el sprint cambia lifecycle/live logs UI, browser real una vez, tres consolas foreground. El operador no debe ejecutar manualmente los tests de la story para sustituir a DevPilot; debe usar la UI/API del producto bajo prueba.

## Regresión

**Full = 0.** Focal + Test Impact + acumulativa A→B + gates proporcionales.

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

- solo jobs tipados allowlisted;
- lifecycle observable y reentrante;
- cancel/timeout sin procesos huérfanos;
- logs redacted;
- failures accionables, no convertidos en PASS;
- S0/S1=0.

Salida: autoriza GSDLC-10-C.
