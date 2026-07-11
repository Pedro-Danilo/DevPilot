---
doc_id: POST-H-032-B-LOCAL-LLM-PROVIDER-HARDENING-REPORT
title: "POST-H-032-B — Local LLM provider hardening report"
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: approved
---

# POST-H-032-B — Local LLM provider hardening report

## Resultado

`POST-H-032-B` queda implementado como `implemented-initial/local-llm-provider-hardening`.

## Capacidades agregadas

- `LocalLlmProviderHealthReport` para validar el hardening local de Ollama y LM Studio.
- Política versionada `.devpilot/modeling/local_llm_provider_health_policy.json`.
- Módulo `src/devpilot_core/modeling/local_provider_health.py`.
- CLI `python -m devpilot_core model local-health --json`.
- ApplicationService `ApplicationService.local_llm_provider_health`.
- Validación de que Ollama/LM Studio permanecen disabled por defecto, localhost-only, sin API key, sin external API, con costo local cero y fallback a `mock` explícito.

## No-go gates preservados

- No external API by default.
- No provider local enabled por defecto.
- No endpoint no-localhost para providers locales.
- No secretos ni API keys en providers locales.
- No dependencia de servidores Ollama/LM Studio reales para tests.
- No remote execution, connector write ni plugin execution.

## Limitaciones

Esta primera versión no instala Ollama ni LM Studio, no descarga modelos, no abre sockets remotos y no promueve agentes a ejecución LLM autónoma. Los providers locales siguen siendo opt-in y las APIs externas quedan para POST-H-032-C con ADR y piloto gated.

## Verificación focal

```powershell
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_032_local_llm_provider_hardening.py `
  tests/test_model_adapter.py `
  tests/test_model_governance.py `
  tests/test_provider_config_schema.py `
  tests/test_ollama_adapter.py `
  tests/test_lmstudio_adapter.py `
  tests/test_policy_engine.py `
  -q
```

## Comandos operacionales

```powershell
python -m devpilot_core model local-health --json
python -m devpilot_core model local-health --json --write-report
python -m devpilot_core schema validate --schema-id LocalLlmProviderHealthReport --instance outputs\reports\local_llm_provider_health_report.json --json
```
