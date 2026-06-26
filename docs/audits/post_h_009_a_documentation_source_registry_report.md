# POST-H-009-A — Documentation source registry report

Estado: `implemented-initial`.

## Objetivo

Crear el primer registry canónico de fuentes documentales de DevPilot y registrar los schemas necesarios para validación estructural.

## Artefactos principales

```text
.devpilot/docs_governance/source_registry.json
docs/schemas/documentation_source_registry.schema.json
docs/schemas/documentation_governance_report.schema.json
src/devpilot_core/docs_governance/
```

## Controles implementados

```text
- Registry local-first, read-only y versionado.
- Clasificación source-of-truth / machine-readable-source / derived.
- Owner, status_required y required_tests obligatorios por entrada.
- Pair explícito roadmap Markdown ↔ roadmap JSON.
- Schemas registrados en docs/schemas/schema_catalog.json.
- Test contract v1/v2 para POST-H-009-A.
```

## Seguridad

```text
network_used=false
external_api_used=false
mutations_performed=false
source_mutations_performed=false
llm_judge_used=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## Límites

Esta versión no implementa aún `docs-governance validate`, validación de frontmatter/status, detección de drift Markdown ↔ JSON ni subgate de quality gate. Esas capacidades corresponden a `POST-H-009-B` a `POST-H-009-E`.
