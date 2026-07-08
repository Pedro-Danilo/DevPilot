---
doc_id: "POST-H-028-A-API-CONTRACT-DRIFT-REPORT"
title: "POST-H-028-A — API contract drift guard report"
status: "approved"
version: "1.0.0"
owner: "Ordonez"
updated: "2026-07-08"
approval: "approved"
phase: "POST-FASE-H"
backlog: "POST-H-028_ui_api_local_hardening"
micro_sprint: "POST-H-028-A"
---

# POST-H-028-A — API contract drift guard report

## 1. Dictamen

POST-H-028-A queda implementado como `implemented-initial`. El micro-sprint agrega un guard determinístico, schema-backed y local-first para bloquear drift entre la API FastAPI ensamblada, el inventario canónico de rutas, el `ApiRouteContractRegistry`, `API_ROUTE_POLICIES` y el OpenAPI estático versionado.

La implementación no abre sockets, no arranca servidor, no llama handlers de negocio, no usa red, no usa APIs externas, no ejecuta LLM judge y no muta archivos fuente.

## 2. Implementado

- `src/devpilot_core/interfaces/api/contract_drift.py`: runner principal `ApiContractDriftGuard`.
- `docs/schemas/api_contract_drift_report.schema.json`: contrato `ApiContractDriftReport`.
- `python -m devpilot_core api contract-drift --json --write-report`: comando CLI.
- `api-contract-drift-guard`: subgate en `quality-gate run --profile hardening|industrial`.
- `docs/07_interfaces/openapi_v1.json`: documento OpenAPI sincronizado con el runtime local vigente.

## 3. Implementado inicial

- La comparación OpenAPI es estática y bloquea contradicciones de rutas no públicas; las rutas públicas de transporte generadas por FastAPI pueden aparecer como warning no bloqueante.
- La protección de rutas se valida contra metadata contractual; POST-H-028-B debe endurecer pruebas negativas de auth/CORS local.

## 4. Contrato

El reporte `ApiContractDriftReport` exige:

- `summary.decision` como `PASS` o `BLOCK`;
- cinco checks: route inventory, policy binding, response contracts, static OpenAPI y no-go gates;
- flags de seguridad local-first/read-only/dry-run;
- findings normalizados mediante `Finding`.

## 5. Definido/no implementado

- No se implementan pruebas visuales ni browser automation.
- No se implementa login multiusuario, OIDC, rate limiting industrial ni API remota.
- No se exponen acciones sensibles nuevas por UI/API.

## 6. No iniciado

- POST-H-028-B — Local auth and CORS hardening.
- POST-H-028-C — Visual smoke tests.
- POST-H-028-D — Operator flows and error states.
- POST-H-028-E — UI route registry enforcement.

## 7. Bloqueado por diseño

- remote execution;
- connector write;
- plugin execution;
- patch apply desde UI;
- rollback execute desde UI;
- external APIs obligatorias;
- SaaS/multiusuario/enterprise auth.

## 8. Criterios PASS

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core api contract-drift --json --write-report
python -m devpilot_core schema validate --schema-id ApiContractDriftReport --instance outputs/reports/api_contract_drift_report.json --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_028_api_contract_drift_guard.py tests/test_api_contract.py tests/test_schema_registry.py tests/test_project_global_state.py -q
```

## 9. Criterios BLOCK

- Ruta FastAPI runtime no registrada.
- Ruta registrada pero ausente en runtime.
- Ruta protegida sin token/policy binding.
- Ruta ApplicationService-backed sin `ApplicationResponse`.
- OpenAPI estático con ruta extra o sin ruta no pública registrada.
- Ruta API con no-go capability activa.

## 10. Riesgos

- El guard no sustituye pruebas HTTP reales; complementa contrato estático/runtime.
- El OpenAPI debe regenerarse cuando se agreguen endpoints.
- Los warnings de `/docs` y `/openapi.json` son aceptables porque son rutas de transporte FastAPI y no endpoints de negocio.
