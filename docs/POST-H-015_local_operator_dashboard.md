---
doc_id: "POST-H-015-IMPLEMENTATION"
id: "POST-H-015"
title: "POST-H-015 — Local operator dashboard"
status: "approved"
version: "0.4.0"
owner: "Ordóñez"
updated: "2026-06-28"
approval: "approved_for_implementation"
phase: "POST-FASE-H"
priority: "P1"
implementation_status: "implemented-initial"
current_micro_sprint: "POST-H-015-C"
next_micro_sprint: "POST-H-015-D"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-015 — Local operator dashboard

## 1. Estado

POST-H-015 queda aprobado para implementación acumulativa después del cierre de `POST-H-014 — UI/API industrial shell`.

El micro-sprint activo implementado es:

```text
POST-H-015-C — ApplicationService/API integration
```

Estado real:

```text
implemented-initial
```

## 2. Alcance de POST-H-015-A

POST-H-015-A define el contrato base para el dashboard local de operador:

```text
docs/schemas/operator_dashboard_snapshot.schema.json
.devpilot/operator/dashboard_config.json
tests/fixtures/operator_dashboard_snapshot.valid.json
```

El contrato exige:

```text
- local_first=true;
- read_only=true;
- dry_run=true;
- network_used=false;
- external_api_used=false;
- mutations_performed=false;
- source_mutations_performed=false;
- remote_execution_enabled=false;
- connector_write_enabled=false;
- plugin_execution_enabled=false;
- secciones obligatorias con status y source_refs.
```

## 3. Alcance de POST-H-015-B

POST-H-015-B implementa la primera capa ejecutable del dashboard:

```text
src/devpilot_core/portfolio/operator_dashboard.py
tests/test_post_h_015_operator_dashboard_aggregator.py
docs/audits/post_h_015_b_operator_dashboard_aggregator_report.md
docs/post_h_015_b_manifest.json
```

Capacidades:

```text
- OperatorDashboardAggregator consolida señales locales de project_state, roadmap, test contracts, quality gates, seguridad, observabilidad, agentes, aprobaciones, release y workspace.
- El snapshot producido respeta OperatorDashboardSnapshot.
- Las fuentes requeridas ausentes bloquean el resultado.
- La evidencia runtime opcional ausente queda como unknown/warn, sin falso PASS.
- write_report=True genera outputs/reports/operator_dashboard_snapshot.json y .md.
- No ejecuta shell, no usa red, no consume APIs externas y no muta fuentes.
```

## 4. Alcance de POST-H-015-C

POST-H-015-C integra el aggregator al boundary ApplicationService/API:

```text
src/devpilot_core/application/operator_dashboard_service.py
src/devpilot_core/interfaces/api/routers/operator.py
tests/test_post_h_015_operator_dashboard_application_api.py
docs/audits/post_h_015_c_operator_dashboard_application_api_report.md
docs/post_h_015_c_manifest.json
```

Capacidades:

```text
- OperatorDashboardApplicationService encapsula OperatorDashboardAggregator.
- ApplicationService expone operator.dashboard.
- GET /api/v1/operator/dashboard devuelve ApplicationResponse.
- La ruta exige token local y policy binding.
- ApiRouteContractRegistry incluye api.operator.dashboard.
- ApplicationOperationCatalog detecta operator.dashboard como operacion API-bound.
- TCR v2 queda corregido para POST-H-015-A/B usando dominio product.ui y C agrega application.service.
```

## 5. Límites explícitos

Esta es una versión `implemented-initial`. Ya existe schema/config, agregador read-only y exposición ApplicationService/API, pero no implementa todavía:

```text
- UI operator dashboard;
- quality gate final del hito.
```

Esas capacidades quedan planificadas para `POST-H-015-D/E`.

## 6. Verificación focal

```bash
PYTHONPATH=src python -m pytest -p no:ddtrace tests/test_post_h_015_operator_dashboard_schema.py -q
PYTHONPATH=src python -m pytest -p no:ddtrace tests/test_post_h_015_operator_dashboard_aggregator.py -q
PYTHONPATH=src python -m pytest -p no:ddtrace tests/test_post_h_015_operator_dashboard_application_api.py -q
PYTHONPATH=src python -c "from pathlib import Path; from devpilot_core.portfolio import OperatorDashboardAggregator, OperatorDashboardAggregatorOptions; r=OperatorDashboardAggregator(Path('.'), OperatorDashboardAggregatorOptions(write_report=True)).build(); print(r.to_dict())"
PYTHONPATH=src python -m devpilot_core schema validate --schema-id OperatorDashboardSnapshot --instance tests/fixtures/operator_dashboard_snapshot.valid.json --json
PYTHONPATH=src python -m devpilot_core schema validate --schema-id OperatorDashboardSnapshot --instance outputs/reports/operator_dashboard_snapshot.json --json
PYTHONPATH=src python -m devpilot_core schema validate --schema-id ApiRouteContractRegistry --instance .devpilot/interfaces/api_route_contract_registry.json --json
```
