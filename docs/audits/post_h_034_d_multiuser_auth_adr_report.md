---
doc_id: "POST-H-034-D-MULTIUSER-AUTH-ADR-REPORT"
title: "POST-H-034-D — Multiuser/auth boundary ADR report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-12"
approval: "approved_by_owner"
micro_sprint: "POST-H-034-D"
preliminary: true
---

# POST-H-034-D — Multiuser/auth boundary ADR report

## Veredicto

POST-H-034-D queda implementado como `implemented-initial` para gobernar la frontera entre auth local y multiuser/auth productivo. La decisión es `continue-blocked`.

## Artefactos producidos

- ADR `docs/adr/ADR-POSTH-034-D-multiuser-auth-boundary.md`.
- Schema `docs/schemas/multiuser_auth_decision.schema.json`.
- Checklist `.devpilot/sensitive_capabilities/multiuser_auth_checklist.json`.
- Manifest `docs/post_h_034_d_manifest.json`.
- Validador `MultiuserAuthAdrValidator` integrado a `SensitiveCapabilityAdrGate`.
- Tests `tests/test_post_h_034_multiuser_auth_adr.py`.

## Controles preservados

```text
multiuser_auth_enabled=false
production_multiuser_enabled=false
multiuser_runtime_enabled=false
iam_enterprise_enabled=false
oidc_enabled=false
sso_enabled=false
session_management_enabled=false
tenancy_enabled=false
tenant_isolation_implemented=false
public_api_enabled=false
network_allowed=false
external_api_allowed=false
credentials_required=false
password_storage_enabled=false
```

## Interpretación industrial

La API local con token, CORS local-only, Identity Registry, RBAC y approvals son controles locales implementados inicialmente. No constituyen IAM enterprise ni autorización para usuarios reales concurrentes. Cualquier cambio hacia usuarios productivos requiere backlog separado, threat model auth, sesiones, no-spoofing, audit trail de usuario real, data isolation y pruebas negativas de bypass.

## Riesgos bloqueados

| Riesgo | Estado |
|---|---|
| Multiuser claim prematuro | Bloqueado |
| IAM enterprise implícito | Bloqueado |
| Public API accidental | Bloqueado |
| OIDC/SSO sin threat model | Bloqueado |
| Tenancy sin aislamiento | Bloqueado |
| Credenciales reales versionadas | Bloqueado |

## Limitaciones

Esta primera versión no implementa login, sesiones, OIDC, SSO, cuentas locales productivas, multi-tenancy ni IAM. Es una frontera arquitectónica verificable para impedir enablement accidental.
