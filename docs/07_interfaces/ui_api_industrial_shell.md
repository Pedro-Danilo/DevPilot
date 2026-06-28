---
doc_id: "POST-H-014-UI-API-INDUSTRIAL-SHELL"
title: "UI/API industrial shell — contrato operativo local"
status: "implemented-initial"
version: "0.2.0"
owner: "Ordóñez"
updated: "2026-06-27"
phase: "POST-H-014-B"
approval: "approved_by_owner"
---

# UI/API industrial shell — contrato operativo local

## Estado

POST-H-014-A implementa la primera capa de la shell industrial local: `ApiRouteContractRegistry`. El objetivo de esta versión no es ampliar funcionalidad de producto ni exponer DevPilot como SaaS, sino contractar la superficie FastAPI existente para que los próximos micro-sprints puedan normalizar respuestas, UI, seguridad y quality gates sin crecimiento accidental.

## Contrato API local

Artefacto canónico:

```text
.devpilot/interfaces/api_route_contract_registry.json
```

Schema:

```text
docs/schemas/api_route_contract_registry.schema.json
```

Validador:

```text
src/devpilot_core/interfaces/api/contracts.py
```

El registry declara por ruta:

```text
method
path
operation
application_service_required
policy_check_required
auth_required
local_only
dry_run_only
mutations_allowed
response_contract
risk_level
owner
remote_execution_allowed
connector_write_allowed
plugin_execution_allowed
external_api_allowed
```

## Invariantes POST-H-014-A

```text
- Toda ruta `/api/v1/*` de FastAPI debe existir en el registry.
- Toda ruta no pública debe estar asociada a ApplicationService.
- Toda ruta sensible debe exigir auth y policy binding.
- Toda ruta ApplicationService-backed debe declarar ApplicationResponse.
- Ninguna ruta puede habilitar remote execution, connector write, plugin execution o external APIs.
- Las únicas mutaciones permitidas en esta fase son de ciclo de vida local de approvals y deben tener justificación explícita.
```


## Response mapping POST-H-014-B

Artefacto canónico:

```text
src/devpilot_core/interfaces/api/response_mapping.py
```

Invariantes añadidas:

```text
- PASS se expone como HTTP 200.
- FAIL se expone como HTTP 400.
- BLOCK se expone como HTTP 403, nunca como HTTP 200 ambiguo.
- ERROR/excepciones técnicas se exponen como HTTP 500 con detalles redactados.
- RequestValidationError se expone como ApplicationResponse con HTTP 422.
- El payload no debe incluir stack traces ni mensajes crudos de excepción.
```

## Límites

Esta capacidad es `implemented-initial`. No sustituye todavía:

```text
- UI Route Contract Registry: POST-H-014-C.
- UI Route Contract Registry: POST-H-014-C.
- Security hardening local adicional: POST-H-014-D.
- Quality gate final UI/API: POST-H-014-E.
```

## Comandos

```powershell
python -m devpilot_core schema validate --schema-id ApiRouteContractRegistry --instance .devpilot/interfaces/api_route_contract_registry.json --json
python -m pytest -p no:ddtrace tests/test_post_h_014_api_route_contracts.py -q
```
