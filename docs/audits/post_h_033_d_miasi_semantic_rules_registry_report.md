---
title: "POST-H-033-D — MIASI semantic rules registry report"
doc_id: POST-H-033-D-MIASI-SEMANTIC-RULES-REGISTRY-REPORT
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: approved
---

# POST-H-033-D — MIASI semantic rules registry report

## Resultado

Estado: `implemented-initial`.

Se implementó el registry schema-backed de reglas semánticas MIASI mediante:

- `docs/schemas/miasi_semantic_rules.schema.json`;
- `.devpilot/miasi/semantic_rules.json`;
- `src/devpilot_core/miasi/declarative_semantic_rules.py`;
- integración progresiva en `src/devpilot_core/miasi/semantic.py`.

La implementación migra únicamente reglas seguras de parametrizar: tokens de side effects, marcadores no-go, tokens de approval/RBAC/SecretGuard/network/local guards, fixtures de evaluación requeridos, severidades y metadata de source/version. No reemplaza el motor semántico completo.

## Propiedades preservadas

- Validación deterministic y local-first.
- No ejecución de agents, tools, red, plugins, conectores ni subprocesses.
- No-go gates remote/plugin/connector preservados.
- Finding IDs históricos preservados.
- Fallback Python temporal preservado.
- Registry inválido no produce pass silencioso.
- Rule source y catalog version quedan visibles en reportes semánticos.

## Alcance preliminar

Esta es una primera versión industrial controlada. El fallback Python sigue siendo obligatorio hasta que POST-H-033 cierre con evidencia before/after suficiente y se pueda retirar sin abrir bypasses. La migración no convierte reglas críticas en configuración desactivable.

## Criterios PASS cubiertos

- Reglas MIASI no-go siguen bloqueando.
- Tokens sensibles y guard mappings quedan versionados.
- Reporte semántico incluye `rule_source` y `catalog_version`.
- Registry inválido activa fallback con finding explícito bloqueante.
- Tests adversariales se mantienen en el set focal.
- El validator sigue sin ejecutar agentes, tools, red, plugins, conectores o subprocesses.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
| --- | --- |
| Registry inválido abre bypass | Fallback seguro + finding BLOCK. |
| Regla crítica desactivable | Schema fuerza `cannot_disable_without_adr=true` y `critical_rules_disable_allowed=false`. |
| Doble fuente temporal | Documentado como compatibilidad preliminar con deprecation target. |
| Relajación de no-go gates | Pruebas adversariales remote/plugin/connector preservadas. |

## Validación focal recomendada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_033_miasi_semantic_rules_registry.py `
  tests/test_miasi_semantic_validator.py `
  tests/test_miasi_semantic_validator_fixtures.py `
  tests/test_miasi_semantic_report_model.py `
  tests/test_miasi_registry.py `
  tests/test_policy_engine.py `
  tests/test_post_h_021_remote_disabled_invariants.py `
  tests/test_post_h_019_plugin_execution_blocked.py `
  tests/test_post_h_018_connector_policy_binding.py `
  -q

python -m devpilot_core schema validate --schema-id MiasiSemanticRules --instance .devpilot\miasi\semantic_rules.json --json
```
