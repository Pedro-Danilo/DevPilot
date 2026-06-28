---
doc_id: "POST-H-014-D-SECURITY-HARDENING-REPORT"
title: "POST-H-014-D — Security hardening local de API/UI"
status: "implemented-initial"
owner: "Ordóñez"
updated: "2026-06-28"
phase: "POST-FASE-H"
---

# POST-H-014-D — Security hardening local de API/UI

## Resultado

POST-H-014-D refuerza la shell local API/UI sin introducir autenticación enterprise, SaaS, despliegue cloud ni ejecución remota.

## Cambios principales

```text
- Nuevo endpoint protegido: GET /api/v1/security/posture.
- ApiRouteContractRegistry actualizado a 33 rutas /api/v1.
- Policy binding agregado para api.security.posture.
- CORS sanitizer local-only: descarta wildcard y orígenes no locales.
- Bind guard: 0.0.0.0/non-local sigue bloqueado incluso con override futuro solicitado.
- Security headers ampliados para respuestas success/error.
- Settings UI consume security posture y escapa/redacta secretos antes de renderizar JSON.
```

## Seguridad

```text
local_first: true
dry_run: true
network_used: false
external_api_used: false
remote_execution_enabled: false
connector_write_enabled: false
plugin_execution_enabled: false
settings_secrets_redacted: true
non_local_bind_allowed: false
remote_bind_override_status: future_disabled_by_design
```

## Pruebas focales

```powershell
python -m pytest -p no:ddtrace tests/test_post_h_014_security_hardening.py tests/test_api_security.py tests/test_api_settings.py tests/test_post_h_014_api_route_contracts.py -q
npm --prefix ui/web test
```

## Limitaciones

Esta es una versión `implemented-initial`. No implementa auth enterprise/OIDC, multiusuario, transporte remoto seguro ni exposición pública. El subgate final `ui-api-industrial-shell` queda para POST-H-014-E.
