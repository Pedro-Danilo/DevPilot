---
doc_id: "ADR-GSDLC-003"
title: "ADR-GSDLC-003 — Local authenticated operator successor boundary"
status: "reviewed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-14"
approval: "pending_owner_00_c_adjudication"
program_id: "DEVPL-GSDLC"
micro_sprint: "DEVPL-GSDLC-00-C"
runtime_implemented: false
historical_multiuser_auth_status: "continue-blocked"
---
# ADR-GSDLC-003 — Local authenticated operator successor boundary

## Contexto

DevPilot posee `identity_registry.json`, RBAC inicial, token API local y approval binding inicial. `ADR-POSTH-034-D` establece correctamente que esto **no es** multiuser/auth productivo y mantiene `multiuser.auth=continue-blocked`.

El Guided SDLC requiere, en GSDLC-02, distinguir operadores locales reales para que un approval no dependa de un `actor_id` aportado por el cliente.

## Decisión

Diseñar un successor **local-only** para operadores autenticados de una sola instalación.

### Identidad

- fuente objetivo: `LocalIdentityRepository`;
- first-run owner local;
- roles derivados server-side;
- unknown actor = deny.

### Credenciales

- nunca plaintext;
- verificador salted/password-hash de grado moderno;
- material sensible protegido por almacenamiento del SO cuando sea viable;
- secretos excluidos de Git, logs y evidence.

### Sesión

- token opaco generado por servidor;
- expiración, revocación y rotación;
- cookie/transport local con controles CSRF para mutaciones;
- sesión vinculada a actor y roles efectivos.

### Approval actor binding

```text
client request
→ authenticated session
→ server principal
→ effective role
→ authorization
→ approval actor binding
```

El cliente no puede declarar ni sustituir el `approver_actor_id`.

## Fuera de alcance

- enterprise IAM;
- tenancy;
- OIDC/SSO;
- public/non-local API;
- federación;
- remote operator auth.

`ADR-POSTH-034-D` permanece como hecho histórico `continue-blocked` hasta que GSDLC-02 implemente y cierre este successor.

## Estado de implementación

`planned-GSDLC`; `multiuser_auth_enabled`, `session_management_enabled`, `public_api_enabled`, `tenancy_enabled` y `iam_enterprise_enabled` siguen en `false`.
