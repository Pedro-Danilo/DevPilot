---
doc_id: "ADR-POSTH-034-D"
title: "POST-H-034-D — Multiuser/auth boundary"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-12"
approval: "approved_by_owner"
decision_status: "continue-blocked"
capability_id: "multiuser.auth"
micro_sprint: "POST-H-034-D"
local_first: true
preliminary: true
multiuser_auth_enabled: false
production_multiuser_enabled: false
multiuser_runtime_enabled: false
iam_enterprise_enabled: false
oidc_enabled: false
sso_enabled: false
session_management_enabled: false
tenancy_enabled: false
tenant_isolation_implemented: false
public_api_enabled: false
network_allowed: false
external_api_allowed: false
credentials_required: false
password_storage_enabled: false
requires_future_enablement_adr: true
requires_future_backlog: true
---

# ADR-POSTH-034-D — Multiuser/auth boundary

## Estado

Aprobada como `continue-blocked`.

POST-H-034-D no habilita multiuser/auth productivo. Esta ADR formaliza la frontera entre los controles locales actuales de DevPilot y cualquier modelo futuro de usuarios reales, sesiones, IAM, tenancy o autenticación federada.

## Contexto

DevPilot cuenta con API local protegida por token local, CORS local-only, identity/RBAC inicial y approval binding. Esos controles son necesarios para el producto local `production-ready-local`, pero no equivalen a IAM enterprise, login multiusuario, tenancy, sesiones productivas ni consola pública.

## Reglas de interpretación obligatorias

```text
local API token exists != production multiuser enabled
identity registry exists != real user identity provider
auth/RBAC initial exists != enterprise IAM
approval actor exists != non-spoofable human account
audit trail exists != tenant/user audit completeness
UI/API local shell exists != enterprise console
POST-H-034-D ADR exists != runtime enablement
```

## Decisión

Mantener `multiuser.auth` en estado `continue-blocked`.

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

## Alternativas evaluadas

| Alternativa | Estado | Motivo |
|---|---|---|
| `continue-blocked` | Aceptada | El alcance actual es local-first, single-owner y no incluye IAM/sesiones/tenancy. |
| `pilot-gated-future` | Pospuesta | Requiere threat model auth, sesiones, RBAC por endpoint, approval binding no spoofable y pruebas de bypass. |
| `approved-for-future-implementation` | Rechazada para el estado actual | Faltan prerequisitos críticos de identidad, sesiones y aislamiento de datos. |
| Habilitación inmediata | Prohibida | Rompería claims locales, controles de seguridad y boundary enterprise/SaaS. |

## Prerrequisitos mínimos para cualquier piloto futuro

- Auth threat model.
- Identity registry productivo o adapter externo controlado.
- Session management, rotación, expiración, revocación y CSRF.
- CORS/token hardening para escenarios no locales.
- RBAC por endpoint, acción, actor y workspace.
- Approval actor binding no spoofable.
- Audit trail con identidad real.
- Tenant/data isolation si se introduce tenancy.
- Secret handling para material de autenticación.
- Tests de bypass auth/RBAC/approval.
- UI auth flow si el producto expone login.

## Criterios PASS

- API local token queda descrito como control local, no como IAM enterprise.
- RBAC/approval local se mantiene como `implemented-initial`.
- No se declara multiuser productivo.
- No se declara enterprise console.
- No se habilita public API, OIDC, SSO, sesiones productivas, tenancy ni credenciales reales.

## Criterios BLOCK

- `multiuser_auth_enabled=true`.
- `production_multiuser_enabled=true`.
- `iam_enterprise_enabled=true`.
- `session_management_enabled=true` sin threat model y tests.
- `tenancy_enabled=true` sin aislamiento de datos.
- API presentada como pública o enterprise-ready.
- Cualquier credencial real versionada.

## Consecuencias

DevPilot conserva su alcance `production-ready-local`. La frontera auth queda gobernada por artefactos verificables y cualquier evolución futura deberá entrar como backlog separado, con ADR de enablement, schema, pruebas negativas, runbook, threat model, control de secretos y quality gate.

## Validación esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_034_multiuser_auth_adr.py -q
python -m devpilot_core schema validate --schema-id MultiuserAuthDecision --instance .devpilot/sensitive_capabilities/multiuser_auth_checklist.json --json
python -m devpilot_core schema validate --schema-id SensitiveCapabilityDecisionMatrix --instance .devpilot/sensitive_capabilities/capability_decision_matrix.json --json
```
