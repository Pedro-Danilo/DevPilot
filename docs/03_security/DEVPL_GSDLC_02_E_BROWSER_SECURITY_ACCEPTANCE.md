---
doc_id: "DEVPL-GSDLC-02-E-BROWSER-SECURITY-ACCEPTANCE"
title: "GSDLC-02-E — Browser authentication and security acceptance contract"
status: "implemented-initial/pending-windows-browser"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-17"
approval: "owner_approved_backlog_scope"
---
# GSDLC-02-E — Browser authentication and security acceptance contract

## Objetivo
Cerrar el journey local `first-run → login → authenticated Project Shell → RBAC/Approval Center → logout/expiry/revoke` sin convertir UI, legacy token o caller parameters en autoridad humana.

## Controles implementados
- First-run owner UI solo cuando no existe owner runtime.
- Login local con password no persistido en frontend.
- Cookie de sesión `HttpOnly`, `SameSite=strict`; CSRF double-submit para mutaciones de sesión.
- Protected-route guard con fail-closed y redirect a `/login`.
- `GET /api/v1/auth/session/status` seguro para recuperación de estados sin actor/roles/secrets.
- Banner persistente de identidad/roles y vista `/account`.
- Rate limit local de login por cliente+hash de username; no persiste el username en la clave.
- Approval Center sigue derivando autoridad de human-session server-side.

## Estados obligatorios de aceptación
first-run, login idle, credencial inválida, owner, developer denegado, security/qa reviewer según matriz, forbidden, expired, revoked, logout, CSRF failure, API unavailable, rate-limited y estado auth desconocido/corrupto fail-closed.

## PASS
Browser real demuestra todos los escenarios requeridos; no hay bypass por URL directa, fuga de credenciales/sesión, role bypass, actor spoof ni S0/S1.

## BLOCK
Cualquier protected route anónima, sesión stale/revoked autorizando, secreto en evidencia, role bypass, segunda full regression o habilitación remote/enterprise.

## Riesgos
El rate limit de esta primera versión es process-local y no constituye defensa distribuida/enterprise. Enterprise IAM, OIDC/SSO, tenancy y remote login permanecen fuera de alcance.

## Verificación
La guía operativa autoritativa del paquete de cierre define los comandos Windows, browser matrix, hashes y la única full regression del backlog.
