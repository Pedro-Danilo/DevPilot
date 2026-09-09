---
doc_id: "PROMPT-DEVPL-GSDLC-10-A"
title: "DEVPL-GSDLC-10-A — Test Impact and test contract UI-native workflow"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-09"
approval: "approved_by_owner/rebound_repo414"
precondition: "DEVPL-GSDLC-09 CLOSED/PASS/WINDOWS-VALIDATED and integrated activation phase PASS"
base_authority_repo: "repo_DevPilot_Local_414_DEVPL_GSDLC_09_FINAL_AUTHORITY_POINTERS_WINDOWS_VALIDATED_CANDIDATE.zip"
base_authority_commit: "adccda6a8fe296a96511bc313be5b883dad32767"
base_authority_sha256: "1ab8b2d38a243ae04caffbf3cd62360c6e613eda3f181cb9d5210b25d549bfe3"
canonical_product_baseline_repo: "repo_DevPilot_Local_413_DEVPL_GSDLC_09_FINAL_CLOSURE_RECONCILIATION_WINDOWS_VALIDATED_CANDIDATE.zip"
full_regression_runs_allowed: 0
browser_policy: "required once if the Validate/TestImpact user journey is materially changed; otherwise prove existing UI contract without duplicate live run"
---

# 01 — GSDLC-10-A

Implementa el flujo UI-native `Story → Validar → Test Impact → StoryTestPlan review/approval` reutilizando la infraestructura existente; **no construir un segundo motor de Test Impact ni una segunda Quality UI**.

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


## Arquitectura/base que debe inspeccionarse antes de modificar

Como mínimo revisar literalmente en repo414 las superficies actuales relacionadas con:
- Test Impact v2 y contratos POST-H-029;
- `src/devpilot_core/application/quality_operations.py`;
- `src/devpilot_core/interfaces/api/routers/quality.py`;
- `ui/web/src/pages/QualityOperationsView.ts`;
- `ui/web/src/pages/StoryCodeWorkbenchView.ts`;
- API client `/quality/test-impact/plan`;
- StoryExecution/SourceChangePlan y hashes/provenance heredados de GSDLC-09;
- Test Contract Registry / Historical Contract Authority.

## Implementación requerida

1. Definir `StoryTestPlan` determinista con al menos:
   - `story_id` / StoryExecution identity;
   - `source_change_plan_id/hash` y changed paths exactos;
   - `test_impact_report_hash`;
   - matched contracts/rules;
   - required tests;
   - recommended tests;
   - unknown/sensitive impact classification;
   - full-regression signal **informativo**, no permiso para lanzar Full;
   - approval/waiver metadata server-side;
   - provenance y timestamps.
2. Desde Story Workbench, `Validar` debe derivar/abrir este plan sin permitir comandos free-form.
3. Reusar Test Impact v2 actual. Unknown path o sensitive delta debe escalar fail-closed según política.
4. Waivers:
   - role-bound;
   - reason obligatorio;
   - expiry;
   - nunca silencian required test sensible sin política explícita;
   - agente/modelo no puede crearlos, aprobarlos ni ampliar su alcance.
5. UI debe explicar **por qué** cada test está required/recommended y mostrar unknowns/sensitive impact de forma accionable.
6. Mantener integración con Project Status/StoryExecution para que el plan pertenezca inequívocamente a una story y a un change-plan hash.
7. Cualquier drift documental menor observado se corrige aquí dentro del mismo delta; no crear sprint/operator independiente.

## Seguridad

- no arbitrary shell;
- no test command libre del usuario;
- no path outside project policy;
- server-side authority para waiver/approval;
- no model-route-to-test-execution authority escalation;
- runtime stores/secrets excluidos de report/evidence.

## Pruebas obligatorias

- delta conocido → contracts/tests explainable;
- unknown path escalation;
- sensitive path under-testing BLOCK;
- deterministic plan/hash;
- stale change-plan hash BLOCK;
- wrong-role waiver BLOCK;
- expired waiver BLOCK;
- agent cannot waive;
- UI mapping Story→Validate→Test Plan;
- historical/current contract classification;
- Test Impact sobre el source delta real del sprint.

## Browser

Si se introduce/modifica el journey visible `Validar`, demostrarlo una vez en browser real con exactamente tres consolas foreground. No repetir browser solo por correctives internos que no cambien UX demostrada.

## Regresión

**Full Regression = 0.** Ejecutar focal + Test Impact + bounded cumulative predecessor set + gates determinísticos proporcionales.

## Evidencia mínima

- `test_impact_report.json`;
- `story_test_plan.json`;
- source delta manifest;
- historical contract sweep;
- screenshots/verifier solo si browser requerido;
- Git pre/post identity;
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

- plan explainable y hash-bound;
- required tests no pueden omitirse silenciosamente;
- no free-form test execution;
- UI-native journey coherente;
- S0/S1=0.

Salida: autoriza GSDLC-10-B.
