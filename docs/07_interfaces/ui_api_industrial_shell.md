---
doc_id: "POST-H-014-UI-API-INDUSTRIAL-SHELL"
title: "UI/API industrial shell — contrato operativo local"
status: "implemented-initial"
version: "0.4.0"
owner: "Ordóñez"
updated: "2026-06-28"
phase: "POST-H-014-D"
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
- Security hardening local adicional: POST-H-014-D.
- Quality gate final UI/API: POST-H-014-E.
```

## Comandos

```powershell
python -m devpilot_core schema validate --schema-id ApiRouteContractRegistry --instance .devpilot/interfaces/api_route_contract_registry.json --json
python -m pytest -p no:ddtrace tests/test_post_h_014_api_route_contracts.py -q
```


## UI route contract POST-H-014-C

Artefacto canónico:

```text
.devpilot/interfaces/ui_route_contract_registry.json
```

Schema:

```text
docs/schemas/ui_route_contract.schema.json
```

Validador:

```text
src/devpilot_core/interfaces/api/ui_contracts.py
```

Invariantes añadidas:

```text
- Dashboard, Reports, Traces, Approvals y Settings deben tener contrato UI.
- Cada contrato UI debe listar allowed_api_routes existentes en ApiRouteContractRegistry.
- Cada página crítica debe mostrar badges local-first, dry-run/plan-only y no-remote.
- La UI debe mantener visibles estados loading, empty, error y BLOCK/ERROR.
- La UI no puede importar devpilot_core, leer outputs directamente, ejecutar procesos ni exponer acciones destructivas.
```

Límites: esta versión es `implemented-initial`; el routing visual final, hardening local adicional y quality gate integrado quedan para POST-H-014-D/E.

Comandos:

```powershell
python -m devpilot_core schema validate --schema-id UiRouteContractRegistry --instance .devpilot/interfaces/ui_route_contract_registry.json --json
python -m pytest -p no:ddtrace tests/test_post_h_014_ui_shell_contract.py -q
npm --prefix ui/web test
```


## Security hardening local POST-H-014-D

Artefactos canónicos:

```text
src/devpilot_core/interfaces/api/security.py
src/devpilot_core/interfaces/api/routers/security_posture.py
/api/v1/security/posture
```

Invariantes añadidas:

```text
- Toda ruta no pública exige token local y policy binding.
- CORS descarta wildcard y orígenes no locales.
- La API local no puede bindear 0.0.0.0 ni hosts no locales; el override queda future-disabled.
- Security posture es un endpoint protegido y no expone token raw, secretos ni stack traces.
- Settings UI escapa HTML y redacta claves secret-like antes de renderizar JSON.
```

Límites: esta versión es `implemented-initial`; auth enterprise/OIDC, transporte seguro externo y quality gate final quedan fuera de POST-H-014-D.

Comandos:

```powershell
python -m pytest -p no:ddtrace tests/test_post_h_014_security_hardening.py tests/test_api_security.py tests/test_api_settings.py -q
npm --prefix ui/web test
```
