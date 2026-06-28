---
doc_id: "POST-H-014-B-RESPONSE-MAPPING-REPORT"
title: "POST-H-014-B — Response mapping y errores homogéneos"
status: "implemented-initial"
owner: "Ordóñez"
updated: "2026-06-27"
phase: "POST-H-014-B"
approval: "approved_by_owner"
---

# POST-H-014-B — Response mapping y errores homogéneos

## Resultado

Estado: `implemented-initial`.

DevPilot incorpora una capa explícita de response mapping para la API local FastAPI. El objetivo es que las rutas y errores HTTP devuelvan un envelope `ApplicationResponse` consistente y que el código HTTP represente correctamente la semántica DevPilot `PASS/FAIL/BLOCK/ERROR`.

## Artefactos

```text
src/devpilot_core/interfaces/api/response_mapping.py
src/devpilot_core/interfaces/api/models.py
src/devpilot_core/interfaces/api/app.py
src/devpilot_core/interfaces/api/security.py
tests/test_post_h_014_response_mapping.py
```

## Mapeo HTTP

```text
PASS  -> 200
FAIL  -> 400
BLOCK -> 403
ERROR -> 500
Request validation -> 422
Unauthorized token -> 401
```

## Seguridad

```text
- No se habilita red externa.
- No se habilitan APIs externas.
- No se habilita remote execution.
- No se habilita connector write.
- No se habilita plugin execution.
- Las excepciones técnicas no exponen stack traces ni mensajes crudos.
```

## Evidencia de pruebas esperada

```powershell
python -m pytest -p no:ddtrace tests/test_post_h_014_response_mapping.py tests/test_api_local.py tests/test_api_security.py tests/test_api_approvals_actions.py tests/test_api_reports_traces.py tests/test_api_settings.py tests/test_post_h_014_api_route_contracts.py -q
python -m pytest -p no:ddtrace tests/test_schema_registry.py tests/test_project_global_state.py tests/test_test_contract_registry.py tests/test_test_contract_registry_v2.py tests/test_test_contract_registry_profiles_v2.py -q
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```

## Limitaciones

POST-H-014-B no implementa UI route registry, UX visual de estados, hardening adicional de API local ni quality-gate final. Esos puntos quedan para POST-H-014-C/D/E.
