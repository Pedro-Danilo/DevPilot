---
title: "POST-H-033-E — Policy/guard pattern catalogs report"
doc_id: POST-H-033-E-POLICY-GUARD-PATTERN-CATALOGS-REPORT
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: approved
---

# POST-H-033-E — Policy/guard pattern catalogs report

## Resultado

Estado: `implemented-initial`.

Se implementó el catálogo schema-backed de patrones de guards de seguridad mediante:

- `docs/schemas/policy_guard_pattern_catalog.schema.json`;
- `.devpilot/policy/guard_pattern_catalog.json`;
- `src/devpilot_core/policy/guard_catalog.py`;
- integración con `PromptInjectionGuard`, `ToolInjectionGuard` y `SecretGuard`.

La implementación no convierte las defensas críticas en configuración débil. Los patrones built-in mandatory permanecen no removibles en Python y el catálogo solo puede agregar extensiones locales o reflejar la base obligatoria validada por schema y checks semánticos.

## Propiedades preservadas

- Validación deterministic y local-first.
- Sin LLM judge.
- Sin red, API externa, remote execution, connector write, plugin execution, subprocesses, agents ni tools.
- Payloads redactados en findings y metadata.
- SecretGuard mantiene redacción de claves y valores sensibles.
- PromptInjectionGuard y ToolInjectionGuard conservan finding IDs históricos.
- Catálogo inválido falla cerrado y no abre bypass.
- Catálogo faltante activa fallback Python temporal no bloqueante.

## Alcance preliminar

Esta es una primera versión industrial controlada. El fallback Python sigue siendo obligatorio hasta que POST-H-033 cierre con evidencia before/after suficiente. El catálogo puede extender patrones, pero no deshabilitar ni debilitar patrones críticos. Cualquier cambio para reducir severidad o permitir desactivar defensas críticas requiere ADR/backlog explícito.

## Criterios PASS cubiertos

- No se puede deshabilitar una regla crítica sin ADR/backlog.
- Catálogo valida contra `PolicyGuardPatternCatalog`.
- Tests adversariales de prompt injection, tool injection y secrets se mantienen.
- Payloads siguen redactados.
- Catálogo inválido bloquea en modo fail-closed.
- Pattern extensions reportan `rule_source` y `catalog_version`.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
| --- | --- |
| Catálogo inválido abre bypass | Fallback seguro + finding/decisión BLOCK. |
| Regla crítica desactivable | Schema + validación semántica exigen `built_in_mandatory=true` y `cannot_disable_without_adr=true`. |
| Extensión local reduce severidad | Las extensiones no pueden modificar mandatory IDs; el loader bloquea drift de mandatory patterns. |
| Payload crudo en findings | Metadata reporta categorías/reglas, no texto original. |
| Doble fuente temporal | Documentada como compatibilidad preliminar con target de deprecación. |

## Validación focal recomendada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_033_policy_guard_pattern_catalogs.py `
  tests/test_prompt_injection_guard.py `
  tests/test_secret_guard_hardening.py `
  tests/test_policy_engine.py `
  tests/test_policy_engine_approval_rbac_enforcement.py `
  tests/test_post_h_032_tool_calling_contract.py `
  -q

python -m devpilot_core schema validate --schema-id PolicyGuardPatternCatalog --instance .devpilot\policy\guard_pattern_catalog.json --json
python -m devpilot_core schema validate --schema-id PolicyGuardPatternCatalog --instance docs\post_h_033_e_manifest.json --json
```
