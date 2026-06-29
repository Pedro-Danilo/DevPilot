---

doc_id: "POST-H-015-BACKLOG"
id: "POST-H-015"
title: "POST-H-015 — Local operator dashboard"
status: "approved"
version: "0.3.0"
owner: "Ordóñez"
updated: "2026-06-28"
approval: "approved_for_implementation"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
implementation_status: "implemented-initial"
current_micro_sprint: "POST-H-015-B"
next_micro_sprint: "POST-H-015-C"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-015 — Local operator dashboard

## 1. Objetivo

Construir un **dashboard local de operador** que permita visualizar de forma integrada el estado operacional de DevPilot: madurez, gates, test contracts, riesgos, observabilidad, workspace, agentes, aprobaciones, release dry-run y roadmap activo.

Este dashboard no reemplaza `POST-H-002`; lo consume. `POST-H-002` crea el maturity dashboard basado en assessment. `POST-H-015` crea una consola de operador local para el trabajo diario.

## 2. Contexto y justificación

DevPilot ya genera abundante evidencia local:

```text
outputs/reports/*.json
outputs/traces/events.jsonl
.devpilot/project_state.json
.devpilot/testing/test_contract_registry.json
.devpilot/evals/*.json
.devpilot/miasi/*.json
quality-gate hardening
industrial-readiness check
agentops status
approval list
release verify
```

El problema es que la evidencia está distribuida. Un operador necesita una vista única para decidir:

```text
¿Puedo avanzar?
¿Qué está bloqueado?
¿Qué cambió desde el último run?
¿Qué riesgos están activos?
¿Qué gates fallaron?
¿Qué comandos debo ejecutar ahora?
¿Qué backlog/hito está vigente?
```

## 3. Alcance

Incluye:

```text
- Dashboard local read-only por defecto.
- Widgets/cards de estado operacional.
- Resumen de madurez y roadmap.
- Estado de quality gates/test contracts/project state.
- Señales de observabilidad y runtime hygiene.
- Estado de agentes/MIASI/approvals.
- Estado release dry-run.
- Recomendaciones de siguiente comando local.
- Export local JSON/Markdown del dashboard.
```

No incluye:

```text
- Control plane remoto.
- Monitoring cloud.
- Multiusuario enterprise.
- Ejecución destructiva desde dashboard.
- Botones para connector write, plugins o remote.
- Sustituir los reportes fuente.
```

## 4. Fuentes de entrada obligatorias

```text
POST-H-002 maturity dashboard outputs
.devpilot/project_state.json
.devpilot/testing/test_contract_registry.json
.devpilot/evals/post_h_eval_001_prioritized_roadmap.json
docs/backlogs/post_h_prioritized_roadmap.md
docs/03_security/post_h_security_risk_register.md
outputs/reports/
outputs/traces/events.jsonl
src/devpilot_core/quality/gate.py
src/devpilot_core/industrial/readiness.py
src/devpilot_core/observability/
src/devpilot_core/approval/
src/devpilot_core/agents/
src/devpilot_core/release/
ui/web/src/pages/Dashboard.ts
```

## 5. Entregables

```text
docs/schemas/operator_dashboard_snapshot.schema.json
.devpilot/operator/dashboard_config.json
src/devpilot_core/portfolio/operator_dashboard.py
src/devpilot_core/application/operator_dashboard_service.py
src/devpilot_core/interfaces/api/routers/operator.py
ui/web/src/pages/OperatorDashboard.ts
ui/web/src/components/OperatorStatusCard.ts
ui/web/src/components/OperatorGatePanel.ts
ui/web/src/components/OperatorNextActions.ts
tests/test_post_h_015_operator_dashboard.py
tests/test_post_h_015_operator_dashboard_schema.py
docs/05_operations/local_operator_dashboard_runbook.md
outputs/reports/operator_dashboard_snapshot.json   # generado, no versionable
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/application/services.py
src/devpilot_core/interfaces/api/app.py
ui/web/src/main.ts
.devpilot/testing/test_contract_registry.json
```

## 6. Modelo de datos mínimo

```json
{
  "schema_version": "1.0",
  "snapshot_id": "operator-dashboard-20260623T000000Z",
  "workspace_id": "devpilot-local",
  "generated_at_utc": "2026-06-23T00:00:00Z",
  "local_first": true,
  "read_only": true,
  "network_used": false,
  "external_api_used": false,
  "mutations_performed": false,
  "sections": {
    "maturity": {"status": "pass", "score": 84.18},
    "quality_gates": {"status": "pass", "blocking_findings_total": 0},
    "test_contracts": {"status": "pass", "contracts_total": 86},
    "roadmap": {"active_hito": "POST-H-002", "next_hito": "POST-H-003"},
    "security": {"no_go_active": false},
    "observability": {"retention_policy_present": false},
    "agents": {"runtime_status": "implemented-initial"},
    "release": {"release_ready": false}
  },
  "recommended_next_actions": [
    {"command": "python -m devpilot_core quality-gate run --profile hardening --json", "reason": "Verify current hardening state"}
  ]
}
```

## 7. Principios de diseño

```text
1. Read-only-first: no mutaciones desde dashboard por defecto.
2. Source-linked: cada dato debe indicar fuente.
3. Operator-oriented: mostrar decisiones accionables, no solo métricas.
4. No hidden risk: no-go gates visibles.
5. Local-only: sin telemetría remota.
6. Deterministic: snapshot reproducible desde fuentes locales.
```

## 8. Micro-sprints propuestos

### POST-H-015-A — Dashboard snapshot schema y config

Objetivo: definir el contrato de snapshot operacional.

Tareas:

```text
1. Crear operator_dashboard_snapshot.schema.json.
2. Crear .devpilot/operator/dashboard_config.json.
3. Definir secciones obligatorias.
4. Registrar schema en schema_catalog.
5. Crear tests de schema.
```

Criterios PASS:

```text
PASS si el snapshot expresa local_first, read_only y mutations_performed=false.
PASS si cada sección tiene status y source_refs.
PASS si existe configuración local versionada.
```

Estado de implementación: `implemented-initial`.

Artefactos creados por POST-H-015-A:

```text
docs/schemas/operator_dashboard_snapshot.schema.json
.devpilot/operator/dashboard_config.json
tests/fixtures/operator_dashboard_snapshot.valid.json
tests/test_post_h_015_operator_dashboard_schema.py
docs/05_operations/local_operator_dashboard_runbook.md
docs/audits/post_h_015_a_operator_dashboard_schema_config_report.md
docs/post_h_015_a_manifest.json
docs/POST-H-015_local_operator_dashboard.md
```

Alcance real aplicado:

```text
- Se aprueba POST-H-015 para implementación controlada.
- Se registra el contrato OperatorDashboardSnapshot en schema_catalog.
- Se define configuración local read-only para secciones, fuentes y acciones recomendadas.
- Se agrega fixture de snapshot válido para validación CLI temprana.
- No se implementa todavía aggregator, ApplicationService, API ni UI; eso queda para POST-H-015-B/C/D.
```

Limitación explícita:

```text
POST-H-015-A es una primera versión contractual. No genera snapshots desde fuentes reales todavía.
El snapshot real bajo outputs/reports/operator_dashboard_snapshot.json debe ser producido por el aggregator read-only en POST-H-015-B.
```

### POST-H-015-B — Aggregator read-only de señales operacionales

Objetivo: construir un agregador local determinístico.

Tareas:

```text
1. Implementar operator_dashboard.py.
2. Leer project_state, test contracts, quality gate summaries, roadmap y reports.
3. Tolerar fuentes ausentes con status unknown, no ERROR salvo fuente obligatoria.
4. Añadir source_refs por métrica.
5. Producir snapshot JSON.
```

Criterios PASS:

```text
PASS si el aggregator no muta archivos.
PASS si no usa red ni APIs externas.
PASS si reporta fuentes ausentes de forma explícita.
```

Estado de implementación: `implemented-initial`.

Artefactos creados por POST-H-015-B:

```text
src/devpilot_core/portfolio/operator_dashboard.py
tests/test_post_h_015_operator_dashboard_aggregator.py
docs/audits/post_h_015_b_operator_dashboard_aggregator_report.md
docs/post_h_015_b_manifest.json
```

Alcance real aplicado:

```text
- Implementa OperatorDashboardAggregator como componente local read-only.
- Lee .devpilot/operator/dashboard_config.json y fuentes locales versionadas.
- Agrega señales de maturity, quality_gates, test_contracts, roadmap, security, observability, agents, approvals, release y workspace.
- Bloquea cuando falta una fuente requerida.
- Tolera evidencia runtime opcional ausente como unknown/warn, no como falso PASS.
- Escribe outputs/reports/operator_dashboard_snapshot.json y .md solo cuando write_report=True.
- Mantiene network_used=false, external_api_used=false, mutations_performed=false y source_mutations_performed=false.
```

Limitación explícita:

```text
POST-H-015-B es una primera versión de agregación operacional. No expone ApplicationService, API, CLI público, UI ni quality gate final.
POST-H-015-C debe integrar el aggregator al boundary ApplicationService/API sin bypass.
```

### POST-H-015-C — ApplicationService/API integration

Objetivo: exponer el snapshot a CLI/API sin bypass.

Tareas:

```text
1. Crear OperatorDashboardApplicationService.
2. Integrar en ApplicationService.
3. Crear router API /operator/dashboard.
4. Agregar contrato de ruta para POST-H-014 si ya existe.
5. Crear tests de boundary.
```

Criterios PASS:

```text
PASS si CLI/API usan ApplicationService.
PASS si API route es read-only.
PASS si response es ApplicationResponse.
```

### POST-H-015-D — UI operator dashboard

Objetivo: crear vista UI para operador local.

Tareas:

```text
1. Crear OperatorDashboard.ts.
2. Crear cards por sección.
3. Mostrar no-go gates y next actions.
4. Mostrar timestamps y fuente de cada dato.
5. Agregar smoke tests.
```

Criterios PASS:

```text
PASS si el operador ve estado global en una pantalla.
PASS si fallos BLOCK/ERROR son visualmente claros.
PASS si las acciones sugeridas son comandos dry-run/locales.
```

### POST-H-015-E — Quality gate y runbook operacional

Objetivo: integrar dashboard al flujo de operación local.

Tareas:

```text
1. Agregar subgate operator-dashboard-ready.
2. Actualizar runbook.
3. Crear reporte Markdown del snapshot.
4. Actualizar test contract registry.
```

Criterios PASS:

```text
PASS si el dashboard puede generarse desde CLI.
PASS si el runbook explica interpretación de estados.
PASS si quality gate detecta snapshot inválido.
```

## 9. Comandos esperados

```powershell
python -m devpilot_core operator dashboard --json --write-report
python -m devpilot_core schema validate --schema-id OperatorDashboardSnapshot --instance outputs/reports/operator_dashboard_snapshot.json --json
python -m pytest tests/test_post_h_015_operator_dashboard.py -q
python -m pytest tests/test_post_h_015_operator_dashboard_schema.py -q
python -m devpilot_core quality-gate run --profile hardening --json
```

## 10. Criterios BLOCK

```text
BLOCK si el dashboard muta estado por defecto.
BLOCK si oculta no-go gates.
BLOCK si recomienda comandos con remote execution.
BLOCK si no declara fuentes por métrica.
BLOCK si muestra como PASS una fuente ausente crítica.
```

## 11. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Dashboard ornamental sin decisión operacional | Alta | Next actions y source refs obligatorios. |
| Falso PASS por fuente ausente | Alta | Estado unknown explícito. |
| Duplicación con POST-H-002 | Media | POST-H-015 consume POST-H-002, no lo reemplaza. |
| UI oculta riesgo | Alta | No-go panel obligatorio. |

## 12. Definition of Done

```text
[ ] Snapshot schema validado.
[ ] Aggregator local read-only implementado.
[ ] CLI/API/Service integrados.
[ ] UI OperatorDashboard implementada.
[ ] No-go gates visibles.
[ ] Runbook aprobado.
[ ] Tests y quality gate pasan.
```
