---
doc_id: DEVPL-GSDLC-02-C-SERVER-RBAC
title: Server-side RBAC enforcement
status: pass-candidate/pre-windows
version: 1.0.0
owner: Ordóñez
updated: 2026-08-17
---
# Server-side RBAC enforcement

GSDLC-02-C introduces deterministic authorization between authenticated-session resolution and PolicyEngine/router dispatch.

Authority chain:
`session cookie → LocalAuthService → AuthenticatedPrincipal → RBACApplicationService → ServerRBACEnforcer → PolicyEngine → handler`.

Unknown routes, actions, roles and workspace scopes fail closed. The legacy local token is an explicitly classified compatibility principal and is never human approval authority.

This is the first production-oriented local RBAC enforcement version. It remains deliberately local-only; enterprise IAM, OIDC/SSO, tenancy and remote login remain out of scope. Approval role/risk binding is completed in 02-D and browser role UX in 02-E.
