---
doc_id: "DEVPL-POST-H-EVAL-002-02-BACKLOG"
id: "POST-H-EVAL-002-02"
title: "POST-H-EVAL-002-02 — SDLC real, implementación y trazabilidad"
status: "approved"
version: "1.6.1"
owner: "Ordóñez"
updated: "2026-08-02"
approval: "approved_by_owner"
phase: "POST-H-EVAL-002"
priority: "P0"
roadmap_wave: "EVAL-002-02"
roadmap_source: "docs/00_product/POST-H-EVAL-002_end_to_end_product_pilot_roadmap.md"
source_repo: "repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip"
source_repo_identity_policy: "resolve-from-external-immutable-baseline-manifest"
source_repo_manifest_path: "D:\\Projects\\DevPilot_Artifacts\\POST-H-EVAL-002\\baselines\\repo_327\\BASELINE_CURRENT.json"
source_repo_manifest_schema: "devpilot.post_h_eval_002.operational_baseline.v1"
source_repo_sha256_embedded: false
pilot_baseline_repo: "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip"
depends_on: "POST-H-EVAL-002-01 closed/pass"
implementation_status: "active/02-a-authorized"
current_micro_sprint: "POST-H-EVAL-002-02-A"
next_micro_sprint: "POST-H-EVAL-002-02-B"
workspace_id: "inventory-sales-local"
workspace_root: "D:\\Projects\\DevPilot_Workspaces\\inventory-sales-local"
evaluation_root: "D:\\Projects\\DevPilot_E2E_Evaluation"
artifacts_root: "D:\\Projects\\DevPilot_Artifacts\\POST-H-EVAL-002"
temporary_root: "D:\\Projects\\DevPilot_Temp"
local_first: true
ui_first: true
dry_run_default: true
---

# POST-H-EVAL-002-02 — SDLC real, implementación y trazabilidad

## 1. Estado vigente y autorización

`active/02-a-authorized`.

La dependencia `POST-H-EVAL-002-01` cerró `CLOSED/PASS` mediante `PILOT-E2E-001-RUN-05B-RERUN-03` y el Sprint 7 de cierre de gobernanza 326 → 327. La entrada mínima gobernada es:

```text
Artefacto lógico:
repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip

Manifest autoritativo externo:
D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\baselines\repo_327\BASELINE_CURRENT.json

DevPilot:
D:\Projects\DevPilot_Local

Workspace:
D:\Projects\DevPilot_Workspaces\inventory-sales-local
```

El commit Git, la ruta física y el SHA-256 del baseline operativo deben resolverse y verificarse desde `BASELINE_CURRENT.json`. El hash del ZIP no se incrusta en este backlog porque el documento forma parte del propio archivo generado mediante `git archive`; hacerlo produciría una referencia circular e inestable.

`inventory-sales-local` todavía no debe existir como workspace materializado al iniciar 02-A. El único micro-sprint autorizado es `POST-H-EVAL-002-02-A`; los micro-sprints B–E permanecen secuenciales y no pueden adelantarse.

El manifest externo debe declarar, como mínimo:

```text
schema_id = devpilot.post_h_eval_002.operational_baseline.v1
artifact_name = repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip
git_commit = commit gobernado de entrada
sha256 = hash real del artefacto
worktree_clean_at_generation = true
authorized_micro_sprint = POST-H-EVAL-002-02-A
```

Si el manifest falta, es inválido, no coincide con el artefacto o declara un repositorio no limpio, 02-A queda en `BLOCK`.

## 2. Precedencia documental

Cuando existan notas históricas que describan estados anteriores, se aplicará esta precedencia:

1. frontmatter vigente del backlog;
2. sección **Estado vigente y autorización**;
3. `.devpilot/project_state.json` y evidencia de cierre más reciente;
4. roadmap y runbook vigentes;
5. notas históricas fechadas, exclusivamente como evidencia forense.

Las notas históricas no revocan una autorización posterior explícita.

## 3. Propósito

Validar que DevPilot puede gobernar un SDLC real con trazabilidad completa y una experiencia UI-first medible, mediante la construcción controlada de `inventory-sales-local`.

## 4. Objetivo

Recorrer onboarding, pre-code, arquitectura, seguridad, asistencia agentic gobernada, implementación por historias y regresión del proyecto piloto, midiendo:

- integración real de DevPilot;
- dependencia residual de CLI;
- trazabilidad requisito → historia → archivos → pruebas → trace/report → commit;
- calidad, seguridad y reproducibilidad operacional.

## 5. Modelo operativo y aislamiento

```text
Web UI  → observar, decidir, revisar y aprobar
IDE/Git → autoría y versionado del workspace
CLI     → bridge explícitamente registrado cuando la UI no cubra la operación
```

Rutas canónicas:

```text
D:\Projects\DevPilot_Local
D:\Projects\DevPilot_E2E_Evaluation
D:\Projects\DevPilot_Workspaces\inventory-sales-local
D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002
D:\Projects\DevPilot_Temp
```

`C:\Users\Pedro\Downloads` es únicamente zona temporal de recepción. No se ejecutan operadores, repositorios ni validaciones desde Downloads.

El repositorio DevPilot y el repositorio del workspace deben permanecer físicamente separados. Un defecto de DevPilot se corrige en un patch y commit de plataforma independiente; nunca se mezcla con el commit del proyecto piloto.

## 6. Política de secuenciación, pruebas y artefactos

1. Cada micro-sprint requiere cierre verificable antes de autorizar el siguiente.
2. Cada historia de 02-D se implementa en una invocación separada y termina con un commit trazable.
3. En 02-A–02-D se usan Test Impact, pruebas focales y validadores pertinentes.
4. La regresión completa de `inventory-sales-local` es obligatoria en 02-E.
5. La regresión completa de DevPilot solo se ejecuta si DevPilot cambia o Test Impact/riesgo residual lo exige.
6. Git es la fuente primaria del workspace. Se genera un ZIP limpio del workspace únicamente en el cierre del micro-sprint cuando sea necesario como baseline o transferencia.
7. No se genera un nuevo ZIP de DevPilot si la plataforma no cambió.
8. Se conserva un único paquete de evidencia autoritativo por micro-sprint. Los intentos BLOCK conservan JSON/log mínimo y no multiplican copias completas.
9. Los ZIP limpios excluyen `.git`, `.venv`, `node_modules`, caches, `outputs`, SQLite operativa, secretos, tokens, HAR bruto y backups runtime.

## 7. Micro-sprints

### POST-H-EVAL-002-02-A — Workspace onboarding and isolation

Entregables autoritativos:

```text
04_workspace_onboarding/bootstrap_dry_run.json
04_workspace_onboarding/bootstrap_execute.json
04_workspace_onboarding/readiness_initial.json
04_workspace_onboarding/registry_validation.json
04_workspace_onboarding/isolation_report.json
04_workspace_onboarding/ui_visibility_report.md
04_workspace_onboarding/workspace_git_identity.json
04_workspace_onboarding/write_boundary_manifest.json
```

Actividades:

1. verificar el cierre de 01 y resolver desde `BASELINE_CURRENT.json` el commit, la ruta y el SHA-256 del baseline 327;
2. registrar espacio libre, rutas y estado inicial;
3. ejecutar bootstrap dry-run sin mutaciones;
4. revisar el plan en Reports UI cuando exista superficie;
5. registrar aprobación humana;
6. materializar en la ruta canónica separada;
7. inicializar o verificar repositorio Git independiente del workspace;
8. ejecutar registry validation e isolation check;
9. verificar escritura exclusivamente dentro del workspace permitido;
10. comprobar visibilidad UI y reconciliar UI ↔ CLI;
11. registrar cada bridge o ausencia como UX-GAP;
12. realizar commit de onboarding/baseline del workspace.

PASS:

- manifest externo 327 válido y baseline verificado por nombre, commit y SHA-256;
- dry-run no mutó disco;
- materialización controlada y aprobada;
- cero escritura fuera del workspace;
- registry/isolation PASS;
- repositorio Git del workspace independiente y limpio después del commit;
- workspace visible en UI o gap clasificado;
- evidencia reproducible;
- `POST-H-EVAL-002-02-B` autorizado.

Gobernanza pendiente no bloqueante: al cierre de 02-A debe reconciliarse, si aún persiste, el campo redundante `post_h_eval_002_current_backlog` a `POST-H-EVAL-002-02`, mediante un cambio de gobernanza de DevPilot separado del commit del workspace.

### POST-H-EVAL-002-02-B — Product, requirements, architecture and security baseline

Entregables versionados en el workspace:

```text
product_vision.md
mvp_scope.md
requirements_specification.md
architecture_document.md
security_threat_model.md
test_strategy.md
ADRs/
traceability_matrix.md
```

Actividades:

- definir IDs estables para requisitos, historias, riesgos, controles, ADRs y pruebas;
- fijar arquitectura React + TypeScript, FastAPI + Python y SQLite local;
- definir boundaries, DTOs, persistencia, errores, observabilidad y backup;
- establecer alcance MVP y exclusiones explícitas;
- modelar amenazas y controles proporcionales al contexto local;
- registrar MIASI/policies aplicables;
- ejecutar validaciones semánticas y `readiness-check --strict`;
- crear commit pre-code inmutable.

PASS:

- frontmatter válido;
- requisitos testeables y sin contradicciones críticas;
- riesgos críticos con controles;
- MIASI PASS;
- readiness strict PASS;
- trazabilidad inicial completa;
- cero código funcional del MVP adelantado;
- `POST-H-EVAL-002-02-C` autorizado.

### POST-H-EVAL-002-02-C — Governed agentic assistance

Objetivo: evaluar capacidades agentic sin confundir evidencia con autonomía.

Rutas de proveedor:

```text
Ruta obligatoria: mock/sin API
Ruta opcional: modelos locales, solo localhost y opt-in
Ruta externa: no autorizada por defecto; requiere decisión separada, CostGuard y evidencia explícita
```

Evaluar:

- capability inventory;
- RAG con citations, freshness e insufficient-evidence;
- memoria opt-in, retención, redacción e independencia de evidencia formal;
- tool calling allowlisted, contract-only y dry-run-first;
- approval binding para acciones de riesgo;
- handoffs multiagente explícitos con supervisor gate;
- límites de iteración/tiempo definidos por policy;
- traces visibles y correlacionables.

Entregables:

```text
05_precode_requirements_architecture_security/agentic_evaluation_matrix.md
05_precode_requirements_architecture_security/rag_grounding_samples.json
05_precode_requirements_architecture_security/tool_call_cases.json
05_precode_requirements_architecture_security/handoff_traces.json
05_precode_requirements_architecture_security/agentic_limits_and_costs.json
```

PASS:

- cero ejecución de herramientas no autorizada;
- fuentes y citas presentes;
- insufficient-evidence bloquea afirmaciones no sustentadas;
- memoria no usada como evidencia formal;
- supervisor y checkpoints humanos respetados;
- sin loops autónomos ilimitados;
- no-go gates intactos;
- `POST-H-EVAL-002-02-D` autorizado.

### POST-H-EVAL-002-02-D — MVP implementation cycles

Historias obligatorias:

```text
INV-001 crear producto
INV-002 registrar entrada
INV-003 registrar salida/ajuste
SAL-001 registrar venta
SAL-002 consultar detalle
REP-001 reporte básico
ALT-001 alerta stock mínimo
OPS-001 backup local
```

Por historia:

1. confirmar requisito, aceptación y dependencias;
2. ejecutar análisis DevPilot, fuentes y plan;
3. ejecutar dry-run y aprobación cuando corresponda;
4. implementar código modular completo y migraciones necesarias;
5. ejecutar pruebas focales según Test Impact;
6. ejecutar code review/patch review;
7. verificar report/trace en UI y registrar bridges;
8. actualizar trazabilidad;
9. crear `06_implementation_cycles/<story-id>/story_execution_record.md`;
10. crear un commit único y trazable de la historia;
11. comprobar no regresión de historias previas.

PASS por historia:

- criterios de aceptación PASS;
- pruebas focales PASS;
- blockers de review = 0;
- trace/report disponible o gap clasificado;
- commit trazable;
- no regresión observada en historias cerradas.

PASS de 02-D:

- ocho historias cerradas;
- flujo funcional mínimo integrado;
- `S0/S1 = 0`;
- `POST-H-EVAL-002-02-E` autorizado.

### POST-H-EVAL-002-02-E — Regression, traceability and UI gap consolidation

Entregables:

```text
07_testing_traceability/test_impact_registry.json
07_testing_traceability/pilot_test_contracts.md
07_testing_traceability/requirement_to_test_matrix.md
07_testing_traceability/full_regression.log
07_testing_traceability/full_regression.junit.xml
07_testing_traceability/critical_flow_e2e.json
11_incidents_and_ux_gaps/cli_bridge_register.md
11_incidents_and_ux_gaps/ui_gap_register.md
```

Validaciones:

- unit, integration, API, contract, UI y E2E;
- flujo producto → entrada → venta → stock → reporte → alerta;
- trazabilidad requisito → historia → archivos → pruebas → trace → commit;
- regresión completa del proyecto piloto;
- quality gate DevPilot pertinente;
- discoverability UI de reportes/traces;
- clasificación completa de CLI bridges y gaps.

PASS:

```text
pilot_regression = PASS
critical_flow = PASS
traceability_coverage = 100%
open_traceability_blockers = 0
S0 = 0
S1 = 0
all_cli_bridges_classified = true
```

El cierre de 02-E debe fijar:

- commit y versión de cierre del workspace;
- baseline de evidencia del backlog 02;
- DevPilot baseline vigente para 03-A;
- decisión `PASS`, `PASS-WITH-GAPS` o `BLOCK`;
- autorización explícita de `POST-H-EVAL-002-03-A` solo cuando corresponda.

## 8. Definition of Done del backlog 02

- A–E cerrados en secuencia;
- workspace aislado y gobernado;
- baseline pre-code PASS;
- capacidades agentic evaluadas con límites;
- ocho historias funcionales trazables;
- regresión del piloto PASS;
- cobertura de trazabilidad 100%;
- UI/CLI gaps consolidados;
- `S0/S1 = 0`;
- baseline de entrada de 03-A identificado y verificado;
- `POST-H-EVAL-002-03` autorizado.

## 9. Registro histórico no autoritativo

Las siguientes entradas se conservan como historia forense y no describen el estado vigente:

- 2026-07-21: Runtime corrective 324 y gate RUN-03;
- 2026-07-22: RUN-03 `BLOCK-WITH-PROGRESS` y corrective 325;
- 2026-07-28: RUN05B RERUN-02 `BLOCK/product-contract-evidence` y corrective 326.

Fueron superadas por `PILOT-E2E-001-RUN-05B-RERUN-03 CLOSED/PASS` y por el cierre de gobernanza repo 327.
