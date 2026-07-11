---
doc_id: "ADR-POSTH-032-C"
title: "ADR-POSTH-032-C — External API provider gated pilot"
status: "proposed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-11"
approval: "proposed_for_owner_review"
decision_state: "proposed"
decision_status: "gated-pilot-design-only"
micro_sprint: "POST-H-032-C"
phase: "POST-FASE-H"
local_first: true
external_api_enabled_by_default: false
real_external_api_calls_enabled: false
fake_provider_required_for_tests: true
requires_future_enablement_adr: true
---

# ADR-POSTH-032-C — External API Provider Gated Pilot

## 1. Contexto

DevPilot mantiene una arquitectura local-first. Los providers `mock`, `ollama` y `lmstudio` cubren ejecución determinística/offline y proveedores locales opcionales. POST-H-032-B endureció Ollama/LM Studio como providers locales disabled-by-default, localhost-only y sin secretos.

El siguiente riesgo arquitectónico es permitir providers API externos —por ejemplo OpenAI o Gemini— sin convertirlos en dependencia operativa, sin exponer secretos y sin romper el claim `production-ready-local`.

## 2. Decisión

Se aprueba una decisión **proposed / design-only / gated-pilot**:

```text
external_api_enabled_by_default=false
real_external_api_calls_enabled=false
fake_provider_required_for_tests=true
external_api_required_for_local_operation=false
external_api_required_for_production_ready_local=false
```

POST-H-032-C puede crear policy, schema, fake provider contract, CostGuard evidence, SecretGuard evidence, CLI/report y pruebas; **no puede** implementar llamadas reales a proveedores externos ni usar red en tests.

## 3. Controles obligatorios antes de cualquier llamada real futura

Una llamada real futura requerirá, como mínimo:

```text
local_non_versioned_opt_in_config=true
env_var_secret_reference_only=true
api_key_value_never_versioned=true
operator_warning_visible=true
risk_report_required=true
CostGuard_external_api_allowed=true
budget_limit_usd > 0
approval_or_operator_acknowledgement=true
SecretGuard_pass=true
PromptInjectionGuard_pass=true
ToolInjectionGuard_pass=true
external_api_used_reported=true
network_used_reported=true
observability_event_emitted=true
no production-ready-local dependency=true
```

## 4. Alternativas evaluadas

| Alternativa | Decisión | Motivo |
|---|---|---|
| Habilitar OpenAI/Gemini directamente | Rechazada | Introduce coste, secretos, red externa y dependencia operacional. |
| Mantener solo mock/local indefinidamente | Rechazada como única ruta | Limita aprendizaje y diseño multi-modelo, pero sigue siendo el default seguro. |
| Crear fake/gated pilot con ADR | Aceptada | Permite diseñar contrato, no-go gates y pruebas sin coste ni red. |
| Permitir llamadas reales en tests si hay API key | Rechazada | Rompe reproducibilidad, introduce costes y fragilidad CI/local. |

## 5. Criterios PASS

```text
external_api_enabled_by_default=false
real_api_call_performed=false
external_api_used=false
network_used=false
api_key_values_in_repo=false
secret_values_read=false
tests_require_real_api=false
fake_provider_contract_ok=true
CostGuard blocks accidental external API by default
operator_warning_required=true
risk_report_required=true
```

## 6. Criterios BLOCK

```text
provider API enabled en config versionada
API key o secret value en repo
cualquier test depende de OpenAI/Gemini/Mistral/HF real
CostGuard bypass para provider externo
warning/risk report ausente
external API usada sin reporte explícito
claim production-ready-local depende de API externa
```

## 7. Consecuencias

- DevPilot gana una ruta de evolución multi-modelo sin coste ni red por defecto.
- El fake provider queda como contrato de integración, no como evidencia de calidad del proveedor real.
- Los providers externos siguen deshabilitados y no son requisito de operación local.
- Una futura activación real exigirá otra decisión de enablement o actualización explícita de esta ADR.

## 8. Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core model external-api-pilot --json
python -m devpilot_core model external-api-pilot --json --write-report
python -m devpilot_core schema validate --schema-id ExternalApiProviderPilot --instance outputs/reports/external_api_provider_pilot_report.json --json
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_032_external_api_provider_pilot.py -q
```

## 9. Estado

`proposed` en POST-H-032-C. Esta ADR existe para bloquear enablement implícito y definir el camino seguro. No autoriza tráfico externo ni lectura de secretos.
