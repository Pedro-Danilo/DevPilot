---
doc_id: "POST-H-006-D-AUDIT"
title: "POST-H-006-D — CLI hotspot and command ownership report"
status: "approved"
updated: "2026-06-25"
owner: "Ordóñez"
---

# POST-H-006-D — CLI hotspot and command ownership report

## Propósito

Documentar la implementación inicial del reporte read-only de hotspots CLI y ownership por comando. El reporte convierte el registry acumulado A/B/C en evidencia operativa para priorizar `POST-H-006-E` y `POST-H-007`.

## Alcance implementado

```text
src/devpilot_core/cli_registry/hotspots.py
src/devpilot_core/cli_registry/report.py
src/devpilot_core/cli_registry/registry.py
outputs/reports/cli_command_registry_report.json
outputs/reports/cli_command_registry_report.md
tests/test_post_h_006_d_cli_hotspot_ownership.py
```

El reporte calcula:

```text
- comandos por dominio;
- comandos por owner_module;
- migrated / registered_only / legacy;
- comandos con side effects;
- comandos high/critical;
- comandos sin boundary explícito fuera de cli.py;
- comandos sin asociación inferida a Test Contract Registry;
- top hotspots por score.
```

## Seguridad

La implementación es read-only/advisory. No ejecuta comandos, no importa handlers de dominio, no activa runtime router, no habilita remote execution, no habilita connector write y no habilita plugin execution.

## Criterios PASS cubiertos

```text
PASS si el reporte diferencia migrated, registered_only y legacy.
PASS si comandos críticos aparecen con risk_level alto/crítico.
PASS si el reporte es read-only y no modifica fuentes.
PASS si los outputs cli_command_registry_report.json/.md se generan solo con --write-report.
PASS si el Test Contract Registry v1/v2 registra la nueva cobertura.
```

## Limitación industrial explícita

Esta versión es preliminar. Todavía no bloquea crecimiento del CLI ni falla por comandos legacy; prepara la evidencia para `POST-H-006-E — Gate de no crecimiento monolítico`. La asociación a test contracts es inferida desde `recommended_tests`, no una prueba de cobertura semántica completa por comando.

## Comandos de validación

```powershell
python -m pytest tests/test_post_h_006_d_cli_hotspot_ownership.py tests/test_post_h_006_c_handler_migration.py tests/test_post_h_006_b_declarative_registry.py tests/test_post_h_006_cli_command_registry.py tests/test_cli_command_registry_schema.py -q
python -m devpilot_core cli-registry report --write-report --json
python -m devpilot_core schema validate --schema-id CliCommandRegistry --instance outputs/reports/cli_command_registry.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```
