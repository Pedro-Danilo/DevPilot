# POST-H-015-B — Operator Dashboard Aggregator Report

## Estado

`implemented-initial`

## Objetivo

Implementar el agregador local read-only de señales operacionales para construir un snapshot compatible con `OperatorDashboardSnapshot`, manteniendo la frontera local-first de DevPilot.

## Artefactos

```text
src/devpilot_core/portfolio/operator_dashboard.py
tests/test_post_h_015_operator_dashboard_aggregator.py
docs/post_h_015_b_manifest.json
docs/audits/post_h_015_b_operator_dashboard_aggregator_report.md
```

## Capacidad implementada

`OperatorDashboardAggregator` lee `.devpilot/operator/dashboard_config.json` y consolida secciones de operador:

```text
maturity
quality_gates
test_contracts
roadmap
security
observability
agents
approvals
release
workspace
```

Cada seccion incluye `source_refs`, metricas locales y estado operacional. Las fuentes requeridas ausentes producen `BLOCK`; las fuentes runtime opcionales ausentes se expresan como `unknown` en secciones y `warn` a nivel de snapshot.

## Seguridad

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

El agregador no ejecuta shell, no inicia servidores, no consulta red y no escribe archivos fuente. Solo escribe reportes bajo `outputs/reports` cuando se solicita explicitamente `write_report=True`.

## Correccion heredada aplicada

`docs/post_h_015_a_manifest.json` se corrige para que `next_sprint` conserve el hito `POST-H-015`. El avance micro queda representado por `next_micro_sprint=POST-H-015-B`, evitando el error de schema donde `POST-H-015-B` no satisface el patron de `next_sprint`.

## Limitaciones

Esta es una primera version de agregacion. No implementa todavia ApplicationService, router API, UI operator dashboard ni quality gate final. Esos alcances permanecen planificados para POST-H-015-C/D/E.
