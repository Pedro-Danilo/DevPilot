---
doc_id: "DEVPL-OPS-LOCAL-OPERATOR-DASHBOARD"
title: "Local Operator Dashboard Runbook"
status: "approved"
version: "0.2.0"
owner: "Ordóñez"
updated: "2026-06-28"
phase: "POST-FASE-H"
related_backlog: "POST-H-015"
current_micro_sprint: "POST-H-015-B"
---

# Local Operator Dashboard Runbook

## POST-H-015-B — Aggregator read-only de señales operacionales

POST-H-015-B agrega `OperatorDashboardAggregator`, que consolida una vista operacional local desde fuentes versionadas y reportes runtime opcionales. El aggregator no ejecuta shell, no llama red, no usa APIs externas y no muta fuentes. Solo escribe bajo `outputs/reports` cuando se solicita explicitamente `write_report=True`.

Generar snapshot local:

```bash
PYTHONPATH=src python -c "from pathlib import Path; from devpilot_core.portfolio import OperatorDashboardAggregator, OperatorDashboardAggregatorOptions; r=OperatorDashboardAggregator(Path('.'), OperatorDashboardAggregatorOptions(write_report=True)).build(); print(r.to_dict())"
```

Validar el snapshot generado:

```bash
PYTHONPATH=src python -m devpilot_core schema validate --schema-id OperatorDashboardSnapshot --instance outputs/reports/operator_dashboard_snapshot.json --json
PYTHONPATH=src python -m pytest -p no:ddtrace tests/test_post_h_015_operator_dashboard_aggregator.py tests/test_post_h_015_operator_dashboard_schema.py -q
```

Interpretacion operativa:

```text
pass    Todas las fuentes requeridas estan presentes y no hay evidencia runtime opcional ausente.
warn    Las fuentes requeridas estan presentes, pero alguna evidencia runtime opcional no existe en el repo limpio.
block   Falta una fuente requerida y el snapshot no debe tratarse como listo para operador.
unknown Estado permitido en secciones individuales cuando falta evidencia opcional.
```

Limitacion: esta version es `implemented-initial`; no expone aun ApplicationService, API, CLI publico, UI ni quality gate final. Es la capa de agregacion que POST-H-015-C/D/E deben reutilizar.

## POST-H-015-A — Dashboard snapshot schema y config

## 1. Propósito

Definir la operación local inicial del dashboard de operador de DevPilot.

POST-H-015-A crea el contrato y la configuración base. Todavía no genera el snapshot operacional real; esa generación queda para `POST-H-015-B — Aggregator read-only de señales operacionales`.

## 2. Artefactos contractuales

```text
docs/schemas/operator_dashboard_snapshot.schema.json
.devpilot/operator/dashboard_config.json
tests/fixtures/operator_dashboard_snapshot.valid.json
```

## 3. Reglas de seguridad

El dashboard local debe conservar estas garantías:

```text
local_first=true
read_only=true
dry_run=true
network_used=false
external_api_used=false
mutations_performed=false
source_mutations_performed=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## 4. Verificación POST-H-015-A

```bash
PYTHONPATH=src python -m pytest -p no:ddtrace tests/test_post_h_015_operator_dashboard_schema.py -q
PYTHONPATH=src python -m devpilot_core schema validate --schema-id OperatorDashboardSnapshot --instance tests/fixtures/operator_dashboard_snapshot.valid.json --json
PYTHONPATH=src python -m devpilot_core schema list --json
PYTHONPATH=src python -m devpilot_core docs-governance validate --json
PYTHONPATH=src python -m devpilot_core test-contracts validate --json
PYTHONPATH=src python -m devpilot_core test-contracts validate-v2 --json
```

## 5. Criterios PASS/BLOCK

PASS:

```text
- El schema OperatorDashboardSnapshot está registrado.
- El fixture válido pasa contra el schema.
- La configuración local existe y lista todas las secciones obligatorias.
- Cada sección del snapshot exige source_refs.
- Las acciones recomendadas son dry-run.
```

BLOCK:

```text
- El snapshot permite mutaciones o red.
- Una sección carece de source_refs.
- La config habilita remote execution, connector write, plugin execution o external APIs.
- El schema no está registrado en schema_catalog.
```

## 6. Limitación

Esta versión es `implemented-initial`: prepara el contrato industrial, pero no reemplaza el aggregator, la API ni la UI final del dashboard.
