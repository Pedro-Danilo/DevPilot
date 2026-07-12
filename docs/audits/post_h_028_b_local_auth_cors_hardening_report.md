---
doc_id: "POST-H-028-B-LOCAL-AUTH-CORS-HARDENING-REPORT"
title: "POST-H-028-B — Local auth and CORS hardening report"
status: "approved"
version: "1.0.0"
owner: "Ordonez"
updated: "2026-07-08"
approval: "approved"
---

# POST-H-028-B — Local auth and CORS hardening report

## 1. Veredicto

POST-H-028-B queda implementado como `implemented-initial` para endurecer la seguridad local de la API/UI sin convertir DevPilot en plataforma enterprise-auth, SaaS ni API remota publica.

## 2. Implementado

- Schema `LocalApiSecurityHardeningReport`.
- Modulo `src/devpilot_core/interfaces/api/security_hardening.py`.
- Comando `python -m devpilot_core api security-hardening --json --write-report`.
- Quality subgate `local-api-security-hardening` en perfiles `hardening` e `industrial`.
- Pruebas negativas de token ausente e invalido.
- Pruebas positivas de token valido para ruta protegida.
- Validacion de CORS local-only, wildcard rechazado y origen no local rechazado.
- Validacion de bloqueo de host `0.0.0.0` aun cuando `DEVPILOT_API_ALLOW_NON_LOCALHOST` este presente.
- Validacion de security headers en respuestas success/error.
- Validacion de redaccion de settings/providers y token en reportes.

## 3. Implementado inicial

- El hardening usa `TestClient` in-process; no levanta servidor real ni abre sockets.
- La verificacion cubre rutas representativas y contratos de seguridad existentes; no reemplaza futuras pruebas visuales ni pruebas E2E de navegador.
- El modelo de token sigue siendo local/ephemeral/env-var; no es IAM enterprise.

## 4. Contrato

PASS requiere:

```text
- protected_without_token_blocked = true
- protected_invalid_token_blocked = true
- protected_valid_token_passed = true
- cors_wildcard_enabled = false
- local_origin_allowed = true
- non_local_origin_rejected = true
- non_local_bind_allowed = false
- remote_bind_override_enabled = false
- security_headers_present = true
- settings_secrets_redacted = true
- token_redacted_in_report = true
- network_used = false
- external_api_used = false
- source_mutations_performed = false
```

BLOCK se emite si una ruta protegida responde sin token, si wildcard CORS queda activo, si un origen no local recibe CORS, si el host no local se habilita por env var, si faltan security headers o si aparece el token crudo en el reporte.

## 5. No iniciado / futuro

- OIDC/SSO.
- Multiusuario enterprise.
- Rate limiting industrial.
- Sesiones persistentes enterprise.
- TLS/mTLS activo.
- Exposicion remota de API.

## 6. Comandos de verificacion

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_028_local_auth_cors_hardening.py `
  tests/test_post_h_014_security_hardening.py `
  tests/test_api_security.py `
  tests/test_api_settings.py `
  tests/test_api_approvals_actions.py `
  tests/test_schema_registry.py `
  tests/test_project_global_state.py `
  -q

python -m devpilot_core api security-hardening --json --write-report
python -m devpilot_core schema validate `
  --schema-id LocalApiSecurityHardeningReport `
  --instance outputs/reports/local_api_security_hardening_report.json `
  --json
```

## 7. Riesgos

- El hardening actual no debe sobredeclararse como autenticacion enterprise.
- Las pruebas visuales y estados de operador siguen pendientes para POST-H-028-C/D.
- El UI route registry enforcement sigue pendiente para POST-H-028-E.


## POST-H-034-D boundary update

La protección por token local, CORS local-only y headers de seguridad siguen siendo controles locales. No equivalen a IAM enterprise, login multiusuario, sesiones productivas, OIDC, SSO, tenancy ni API pública. Cualquier habilitación futura requiere ADR/backlog separado y pruebas de bypass.
