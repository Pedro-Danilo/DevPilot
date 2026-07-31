---
doc_id: "DEVPL-POST-H-EVAL-002-02-BACKLOG"
id: "POST-H-EVAL-002-02"
title: "POST-H-EVAL-002-02 — SDLC real, implementación y trazabilidad"
status: "approved"
version: "1.5.0"
owner: "Ordóñez"
updated: "2026-07-30"
approval: "approved_by_owner"
phase: "POST-H-EVAL-002"
priority: "P0"
roadmap_wave: "EVAL-002-02"
roadmap_source: "docs/00_product/POST-H-EVAL-002_end_to_end_product_pilot_roadmap.md"
source_repo: "repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip"
pilot_baseline_repo: "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip"
depends_on: "POST-H-EVAL-002-01 closed/pass"
implementation_status: "active/02-a-authorized"
current_micro_sprint: "POST-H-EVAL-002-02-A"
next_micro_sprint: "POST-H-EVAL-002-02-B"
local_first: true
ui_first: true
dry_run_default: true
---

# POST-H-EVAL-002-02 — SDLC real, implementación y trazabilidad

## 1. Estado

`active/02-a-authorized`. La dependencia `POST-H-EVAL-002-01` cerró `PASS` mediante `PILOT-E2E-001-RUN-05B-RERUN-03`; repo 327 registra el cierre documental y autoriza el onboarding aislado. No se ha creado todavía `inventory-sales-local`.

## 2. Propósito

Validar que DevPilot puede gobernar un SDLC real con trazabilidad completa y UI-first medible.

## 3. Objetivo

Recorrer onboarding, pre-code, diseño, implementación y pruebas del proyecto `inventory-sales-local`, midiendo la integración real de DevPilot y la dependencia residual de CLI.

## 2. Regla de ejecución

```text
UI para observar/decidir/aprobar
IDE + archivos versionados para autoría
CLI solo como bridge registrado
```

No se permitirá implementar todo el MVP y validar al final. Cada historia debe cerrar con pruebas, trace/report y commit.

## 3. Micro-sprints

### POST-H-EVAL-002-02-A — Workspace onboarding and isolation

Entregables:

```text
04_workspace_onboarding/bootstrap_dry_run.json
04_workspace_onboarding/bootstrap_execute.json
04_workspace_onboarding/readiness_initial.json
04_workspace_onboarding/registry_validation.json
04_workspace_onboarding/isolation_report.json
04_workspace_onboarding/ui_visibility_report.md
```

Actividades:

1. bootstrap dry-run;
2. revisión del plan en Reports UI;
3. aprobación humana;
4. materialización en ruta separada;
5. registro e isolation check;
6. reconciliación UI↔CLI.

PASS:

- no escritura fuera del workspace;
- registry/isolation PASS;
- workspace visible en UI;
- cualquier falta de UI registrada como UX-GAP.

### POST-H-EVAL-002-02-B — Product, requirements, architecture and security baseline

Entregables versionados en el proyecto piloto:

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

- definir historias e IDs estables;
- arquitectura React/FastAPI/SQLite;
- modelo de errores y observabilidad;
- threat model;
- estrategia de pruebas;
- MIASI registries/policy;
- `readiness-check --strict`.

PASS:

- frontmatter válido;
- requisitos aceptables y testeables;
- riesgos críticos con controles;
- MIASI PASS;
- readiness strict PASS.

### POST-H-EVAL-002-02-C — Governed agentic assistance

**Objetivo:** probar capacidades agentic sin confundir evaluación con autonomía.

Evaluar:

- capability inventory;
- RAG context con citations;
- insufficient-evidence;
- memoria opt-in y redacción;
- tool calling allowlisted/dry-run;
- approval binding;
- handoffs multiagente explícitos;
- traces visibles.

Entregables:

```text
05_precode_requirements_architecture_security/agentic_evaluation_matrix.md
05_precode_requirements_architecture_security/rag_grounding_samples.json
05_precode_requirements_architecture_security/tool_call_cases.json
05_precode_requirements_architecture_security/handoff_traces.json
```

PASS:

- cero tool execution no autorizada;
- sources/citations presentes;
- memory no usada como evidencia formal;
- supervisor/human checkpoints respetados;
- no-go gates intactos.

### POST-H-EVAL-002-02-D — MVP implementation cycles

Historias mínimas:

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

Por cada historia:

1. confirmar requisito y aceptación;
2. análisis DevPilot;
3. fuentes y plan;
4. dry-run;
5. aprobación si aplica;
6. implementación humana/controlada;
7. pruebas focales;
8. code/patch review;
9. Test Impact;
10. report/trace en UI;
11. commit.

Entregable por historia:

```text
06_implementation_cycles/<story-id>/story_execution_record.md
```

PASS por historia:

- criterios de aceptación PASS;
- tests focales PASS;
- blockers de review = 0;
- trace/report disponible;
- commit trazable.

### POST-H-EVAL-002-02-E — Regression, traceability and UI gap consolidation

Entregables:

```text
07_testing_traceability/test_impact_registry.json
07_testing_traceability/pilot_test_contracts.md
07_testing_traceability/requirement_to_test_matrix.md
07_testing_traceability/full_regression.log
11_incidents_and_ux_gaps/cli_bridge_register.md
11_incidents_and_ux_gaps/ui_gap_register.md
```

Validaciones:

- unit/integration/API/contract/UI/E2E;
- flujo crítico producto→entrada→venta→stock;
- requirement→story→files→tests→trace→commit;
- full regression del proyecto;
- quality gate DevPilot según contexto;
- UI discoverability de reportes/traces.

PASS:

```text
pilot regression = PASS
traceability coverage = 100%
open traceability blockers = 0
S0/S1 = 0
all CLI bridges classified = true
```

## 4. Definition of Done

- A-E cerrados;
- workspace y pre-code PASS;
- MVP funcional;
- agentic features evaluadas con límites;
- pruebas y trazabilidad completas;
- UI/CLI gaps consolidados;
- `POST-H-EVAL-002-03` autorizado.

## 2026-07-21 — Runtime corrective 324 y gate RUN-03

- Current repository: `repo_DevPilot_Local_324_POST_H_EVAL_002_01_D_RUNTIME_CORRECTIVE.zip`.
- `PILOT-E2E-001-RUN-02` permanece como evidencia `BLOCK`; no habilita el siguiente backlog.
- La autorización de este backlog sigue condicionada al PASS autoritativo de `PILOT-E2E-001-RUN-03` y al cierre formal de POST-H-EVAL-002-01.


## 2026-07-22 — RUN-03 forensic closure and Browser Acceptance Corrective 325

- RUN-03 is preserved as `BLOCK-WITH-PROGRESS`: materialization, R6.2 runtime and lifecycle PASS; formal browser acceptance BLOCK.
- Product corrective: `repo_DevPilot_Local_325_POST_H_EVAL_002_01_D_BROWSER_ACCEPTANCE_CORRECTIVE.zip`.
- Ordinary requests remain bounded to 8000 ms; expensive operations use explicit operation-specific budgets.
- Dry-run and provider-plan surfaces use exclusive `idle/loading/pass/block/timeout/error` states and never retain a previous PASS after timeout/error.
- Provider plan validates the synthetic proposal in memory and performs no provider-file write.
- Retest required: `PILOT-E2E-001-RUN-04`.
- `POST-H-EVAL-002-01-D` remains open and `POST-H-EVAL-002-02-A` remains unauthorized.

## 2026-07-28 — RUN05B RERUN-02 forensic BLOCK and integral corrective 326

- RERUN-02 is preserved as `BLOCK/product-contract-evidence` and forensic-only; `Finalize` is not authorized.
- Product corrective: `repo_DevPilot_Local_326_POST_H_EVAL_002_01_D_RUN05B_INTEGRAL_CORRECTIVE.zip`.
- Dashboard consumes Health, Approval Center states are conditional, Settings fully redacts secret-like fields and state notices are accessible.
- Operator/auditor tooling must be corrected before a new run.
- Required retest: `PILOT-E2E-001-RUN-05B-RERUN-03`.
- `POST-H-EVAL-002-01-D` remains open and `POST-H-EVAL-002-02-A` remains unauthorized.
