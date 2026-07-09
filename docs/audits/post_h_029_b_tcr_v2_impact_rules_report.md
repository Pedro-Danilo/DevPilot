---
doc_id: "POST-H-029-B-IMPACT-RULES-REPORT"
title: "POST-H-029-B — TCR v2 impact rules report"
status: "approved"
approval: "approved"
version: "1.0.0"
owner: "Ordóñez"
created: "2026-07-09"
updated: "2026-07-09"
sprint: "POST-H-029-B"
---

# POST-H-029-B — TCR v2 impact rules report

## Decisión

POST-H-029-B queda implementado como `implemented-initial/local-first`.

Se agregó `TestImpactRuleRegistry` como fuente declarativa y versionada para reglas de impacto TCR v2. Las reglas mapean rutas cambiadas a dominios, perfiles, pruebas recomendadas, comandos permitidos y escalamiento sin ejecutar pruebas desde JSON.

## Alcance implementado

- Schema `SCHEMA-DEVPL-TEST-IMPACT-RULE-REGISTRY-V1`.
- Registry `.devpilot/testing/test_impact_rules.json` con 12 reglas declarativas.
- CLI `python -m devpilot_core test-impact rules --json --write-report`.
- Runner `src/devpilot_core/testing/impact_rules.py`.
- Integración inicial de `TestImpactAnalyzerV2` con el registry de reglas, preservando heurísticas fallback mientras POST-H-029-C/D/E completan recomendaciones, perfil RC y guard histórico.
- Enriquecimiento de TCR v2 para contratos P0/P1 con `owner_domain`, `service_boundary`, `subgate_id` y `schema_ids` cuando aplica.

## Resultado esperado

El registry debe validar con:

```powershell
python -m devpilot_core test-impact rules --json --write-report
python -m devpilot_core schema validate --schema-id TestImpactRuleRegistry --instance .devpilot/testing/test_impact_rules.json --json
```

## Garantías de seguridad

- `tests_executed=false`.
- `network_used=false`.
- `external_api_used=false`.
- `remote_execution_enabled=false`.
- `connector_write_enabled=false`.
- `plugin_execution_enabled=false`.
- `source_mutations_performed=false`.

## Limitación explícita

POST-H-029-B no ejecuta pruebas, no aprueba waivers y no reemplaza `pytest -q`. La selección sigue siendo advisory. POST-H-029-C debe convertir estas reglas en recomendaciones CLI más expresivas y POST-H-029-E debe convertir el criterio de cierre/regresión en guard bloqueante.
