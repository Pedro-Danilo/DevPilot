---
doc_id: "POST-H-014-UI-API-LOCAL-RUNBOOK"
title: "Runbook local UI/API industrial shell"
status: "implemented-initial"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-27"
phase: "POST-H-014-A"
approval: "approved_by_owner"
---

# Runbook local UI/API industrial shell

## POST-H-014-A — Route Contract Registry y API inventory

Objetivo operativo: verificar que la superficie FastAPI local `/api/v1/*` esté contractada antes de endurecer respuestas, UI, seguridad y quality gates.

Comandos de verificación:

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core schema validate --schema-id ApiRouteContractRegistry --instance .devpilot/interfaces/api_route_contract_registry.json --json
python -m pytest -p no:ddtrace tests/test_post_h_014_api_route_contracts.py -q
```

Criterios PASS:

```text
PASS si toda ruta FastAPI `/api/v1/*` aparece en `.devpilot/interfaces/api_route_contract_registry.json`.
PASS si toda ruta no pública exige auth_required=true y policy_check_required=true.
PASS si toda ruta ApplicationService-backed declara response_contract=ApplicationResponse.
PASS si no existe remote_execution_allowed=true, connector_write_allowed=true, plugin_execution_allowed=true ni external_api_allowed=true.
PASS si las rutas con mutations_allowed=true tienen justificación explícita y son solo mutaciones locales de approval lifecycle.
```

Criterios BLOCK:

```text
BLOCK si existe ruta API no registrada.
BLOCK si una ruta registrada no existe en FastAPI.
BLOCK si una ruta sensible no exige auth o policy.
BLOCK si una ruta habilita remote execution, connector write, plugin execution o external APIs.
BLOCK si una mutación carece de justificación local explícita.
```

Límites: esta versión es `implemented-initial`. POST-H-014-A no crea UI route registry, no cambia UX, no normaliza errores HTTP, no agrega auth enterprise y no integra aún un subgate `ui-api-industrial-shell` al quality gate.
