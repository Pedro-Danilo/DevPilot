---
doc_id: "POST-H-032-C-EXTERNAL-API-PROVIDER-PILOT-REPORT"
title: "POST-H-032-C — External API provider ADR and gated pilot report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-11"
approval: "approved_by_owner"
---

# POST-H-032-C — External API provider ADR and gated pilot report

## Resultado

Estado: `implemented-initial / external-api-gated-pilot`.

POST-H-032-C implementa una ruta gobernada para providers API externos sin habilitar llamadas reales. El sprint agrega ADR, policy, schema, fake provider contract, CostGuard evidence, SecretGuard evidence, CLI y ApplicationService boundary.

## Artefactos

- `docs/adr/ADR-POSTH-032-C-external-api-provider-gated-pilot.md`
- `docs/schemas/external_api_provider_pilot.schema.json`
- `.devpilot/modeling/external_api_provider_pilot_policy.json`
- `src/devpilot_core/modeling/external_api_pilot.py`
- `tests/test_post_h_032_external_api_provider_pilot.py`
- `docs/post_h_032_c_manifest.json`

## Seguridad

Invariantes validados:

```text
external_api_enabled_by_default=false
external_api_used=false
network_used=false
real_api_call_performed=false
tests_require_real_api=false
fake_provider_contract_ok=true
secret_handling_env_only=true
secrets_read=false
api_key_values_in_repo_total=0
cost_guard_blocks_accidental_external_api=true
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## Limitaciones

Esta es una primera versión de diseño/gate. No implementa SDKs, no abre sockets, no lee valores de API keys, no envía prompts a proveedores externos y no permite que APIs externas sean requisito de `production-ready-local`.

## Verificación focal

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_032_external_api_provider_pilot.py -q
python -m devpilot_core model external-api-pilot --json
python -m devpilot_core model external-api-pilot --json --write-report
python -m devpilot_core schema validate --schema-id ExternalApiProviderPilot --instance outputs\reports\external_api_provider_pilot_report.json --json
```

## Decisión de cierre

PASS inicial si los comandos focales reportan cero blockers y `ExternalApiProviderPilot` valida contra schema. La activación real de APIs externas queda explícitamente fuera de alcance.
