---
doc_id: "POST-H-014-UI-API-LOCAL-RUNBOOK"
title: "Runbook local UI/API industrial shell"
status: "implemented-initial"
version: "0.3.0"
owner: "Ordóñez"
updated: "2026-06-28"
phase: "POST-H-014-C"
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

## POST-H-014-B — Response mapping y errores homogéneos

Objetivo operativo: verificar que las respuestas de API local usen `ApplicationResponse` y códigos HTTP explícitos.

Comandos de verificación:

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace tests/test_post_h_014_response_mapping.py tests/test_api_local.py tests/test_api_security.py -q
```

Criterios PASS:

```text
PASS si BLOCK retorna HTTP 403, no HTTP 200.
PASS si errores de validación retornan ApplicationResponse con HTTP 422.
PASS si errores técnicos retornan HTTP 500 con stack traces y mensajes crudos redactados.
```

Límites: esta versión es `implemented-initial`; no implementa UI route registry ni quality gate final.



## POST-H-014-C — UI Route Contract y shell de producto

Objetivo operativo: verificar que la Web UI local está contractada y que toda página crítica es local-first, dry-run/plan-only y no-remote.

Comandos de verificación:

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core schema validate --schema-id UiRouteContractRegistry --instance .devpilot/interfaces/ui_route_contract_registry.json --json
python -m pytest -p no:ddtrace tests/test_post_h_014_ui_shell_contract.py tests/test_web_ui_mvp.py tests/test_web_ui_report_trace_viewer.py tests/test_web_ui_approval_center.py tests/test_web_ui_settings.py -q
npm --prefix ui/web test
```

Criterios PASS:

```text
PASS si toda página crítica aparece en UiRouteContractRegistry.
PASS si allowed_api_routes existe en ApiRouteContractRegistry.
PASS si local-first/dry-run/no-remote badges están presentes.
PASS si loading/empty/error y BLOCK/ERROR son visibles.
```

Criterios BLOCK:

```text
BLOCK si la UI referencia rutas no contractadas.
BLOCK si aparecen rutas destructivas como patch/apply, rollback/execute, refactor/execute o git/push.
BLOCK si la UI lee outputs o .devpilot directamente en lugar de consumir API local.
```

Límites: versión `implemented-initial`; POST-H-014-D/E deben completar security hardening y quality-gate final.


## POST-H-014-D — Security hardening local

La operación local debe mantener:

```text
- Host permitido: 127.0.0.1, localhost o ::1.
- Token obligatorio para rutas no públicas.
- CORS restringido a orígenes locales explícitos; wildcard queda bloqueado.
- Endpoint protegido /api/v1/security/posture para diagnóstico redacted.
- Settings UI sin secretos raw; solo nombres de variables de entorno pueden mostrarse.
```

Validación recomendada:

```powershell
python -m pytest -p no:ddtrace tests/test_post_h_014_security_hardening.py tests/test_api_security.py tests/test_api_settings.py -q
```

Límite: no habilita acceso remoto ni autenticación enterprise.
