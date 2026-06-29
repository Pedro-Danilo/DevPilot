---
doc_id: "POST-H-015-IMPLEMENTATION"
id: "POST-H-015"
title: "POST-H-015 — Local operator dashboard"
status: "approved"
version: "0.2.0"
owner: "Ordóñez"
updated: "2026-06-28"
approval: "approved_for_implementation"
phase: "POST-FASE-H"
priority: "P1"
implementation_status: "implemented-initial"
current_micro_sprint: "POST-H-015-A"
next_micro_sprint: "POST-H-015-B"
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
POST-H-015-A — Dashboard snapshot schema y config
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

## 3. Límites explícitos

Esta es una primera versión contractual. No implementa todavía:

```text
- aggregator read-only de señales operacionales;
- ApplicationService;
- router API;
- UI operator dashboard;
- quality gate final del hito.
```

Esas capacidades quedan planificadas para `POST-H-015-B/C/D/E`.

## 4. Verificación focal

```bash
PYTHONPATH=src python -m pytest -p no:ddtrace tests/test_post_h_015_operator_dashboard_schema.py -q
PYTHONPATH=src python -m devpilot_core schema validate --schema-id OperatorDashboardSnapshot --instance tests/fixtures/operator_dashboard_snapshot.valid.json --json
```
