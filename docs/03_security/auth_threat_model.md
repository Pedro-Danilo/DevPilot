---
doc_id: "DEVPL-GSDLC-02-A-AUTH-THREAT-MODEL"
title: "DEVPL-GSDLC-02-A — Local operator authentication threat model"
status: "pass-candidate/pre-windows"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-16"
---

# Local operator authentication threat model

## Scope

Este modelo cubre únicamente la futura capability `local.operator_auth` de una instalación DevPilot local. 02-A no implementa login, sesiones ni credenciales.

## Assets

- human operator identity;
- role/workspace authority;
- credential verifiers;
- opaque sessions;
- CSRF material;
- approval authority;
- auth audit trail;
- local runtime stores.

## Trust boundaries

1. Browser/UI ↔ Local API.
2. Local API ↔ ApplicationService/auth services.
3. Auth services ↔ identity/credential/session stores.
4. AuthenticatedPrincipal ↔ RBAC/Approval authority.
5. DevPilot product ↔ local OS/user account.

El loopback boundary reduce exposición remota, pero **no convierte localhost en trusted input**.

## Principios

- human authority derives from a server-authenticated session;
- deny-by-default;
- session and credential secrets are runtime-only;
- UI is not an authorization authority;
- legacy API token is not a human identity;
- approval actor is not caller-controlled;
- no enterprise/remote claims;
- fail-closed on unknown/corrupt/stale state.

## Threat register

La fuente machine-readable autoritativa es `.devpilot/identity/auth_threat_matrix.json`. Contiene 18 amenazas y 18 controles diseñados con cobertura 100% threat→control→implementation sprint→test/evidence.

Las categorías incluyen credential disclosure/offline cracking, brute force, session fixation/theft/replay, CSRF, CORS/non-local origins, privilege and role escalation, stale privileges, approval actor spoofing, cross-workspace access, legacy-token bypass, direct URL/API bypass, secret leakage, store corruption, owner recovery abuse y accidental enterprise/remote enablement.

## Residual risk at 02-A

Todos los controles son **DESIGNED, not runtime-enforced**. El residual es aceptable únicamente porque 02-A no habilita runtime auth y los no-go existentes continúan activos. La implementación se distribuye B→E y cualquier cierre de GSDLC-02 con un control crítico no implementado queda BLOCK.
