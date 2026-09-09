---
doc_id: "PROMPT-DEVPL-GSDLC-10-C"
title: "DEVPL-GSDLC-10-C — Quality Gate and remediation loop"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-09"
approval: "approved_by_owner/rebound_repo417"
precondition: "GSDLC-10-B CLOSED/PASS/WINDOWS-VALIDATED or controlled validation FAIL with complete evidence"
execution_source_policy: "repo417 immediate Windows-validated successor of GSDLC-10-B corrective-104"
full_regression_runs_allowed: 0
browser_policy: "required for Quality/remediation UX introduced or materially changed"
---
## Execution rebind — repo417

Fuente de verdad obligatoria para esta ejecución: `repo_DevPilot_Local_417_DEVPL_GSDLC_10_B_JOB_CONSOLE_LIVE_REFRESH_WINDOWS_VALIDATED_CANDIDATE.zip` / commit `e8560099596f5d8d006ef37786f60abedb32acf9` / SHA-256 `ca26d91a2f38a4bbdf17a9b68fd1a8894c0545479973ffabfd08bb9156b915bf`. Repo416 y anteriores quedan como historia, no como execution source. FRX v2.4 A/B es current-active; `Full Regression = 0` en 10-C y cualquier drift documental no crítico se absorbe proporcionalmente sin sprint/repo independiente.


# 03 — GSDLC-10-C

Integra findings→remediation→impacted retest hasta `COMMIT_READY` mediante una decisión de calidad determinista. No crear un Quality Gate paralelo: reconciliar/reutilizar los servicios y la UI existentes.

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


## Implementación requerida

1. Crear/elevar `StoryQualityReport` que agregue de forma trazable:
   - required job results;
   - tests/build/lint;
   - review findings;
   - security findings;
   - traceability completeness;
   - policy/waiver decisions;
   - S0/S1/S2/S3 relevantes.
2. `StoryQualityGate` debe producir decisión determinista `PASS|BLOCK` con razones y hashes de inputs.
3. Nunca `COMMIT_READY` si required validation está FAIL/ERROR/PENDING, salvo una policy explícita que realmente permita esa categoría; S0/S1 no se waivan.
4. Waiver governance:
   - server-side role/policy;
   - scope, reason, approver, expiry;
   - no self-approval;
   - agente/modelo no crea/aprueba/amplía waiver.
5. Remediation:
   - manual o propuesta por agente mediante StepActionAdvisor/ToolIntent;
   - termina en las capacidades gobernadas de GSDLC-09 para modificar código;
   - nunca aplica por autoridad del modelo.
6. Retest: recalcular Test Impact sobre el delta posterior a remediation y ejecutar solo impacted validations cuando la política lo permita; no “rerun everything” por comodidad.
7. Mantener provenance `finding → remediation proposal/change plan → retest → resolved/open`.
8. UI debe mostrar blockers por severidad/origen y qué acción desbloquea el gate.
9. Drift documental menor se corrige en este sprint.

## Pruebas

- false-PASS negatives;
- failed required test prevents COMMIT_READY;
- S0/S1 waiver BLOCK;
- expired/wrong-role waiver BLOCK;
- agent cannot waive or self-approve;
- route/model cannot grant Quality authority;
- deterministic decision/hash;
- remediation changes invalidate stale quality report;
- impacted retest scope;
- finding lifecycle/provenance;
- UI blockers/remediation/retest.

## Regresión

**Full = 0.** Focal + Test Impact + acumulativa A→C + HCA/Contract Reconciliation proporcional + gates baratos.

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

- blockers=0 antes de COMMIT_READY;
- no false PASS;
- remediation y retest trazables;
- authority separation intacta;
- S0/S1=0.

Salida: autoriza GSDLC-10-D.
