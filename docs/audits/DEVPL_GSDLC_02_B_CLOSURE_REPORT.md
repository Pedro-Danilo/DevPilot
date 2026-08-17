---
doc_id: DEVPL-GSDLC-02-B-CLOSURE-REPORT
title: DEVPL-GSDLC-02-B — Identity/session candidate closure report
status: pass-candidate/pre-windows
version: 1.0.0
owner: Ordóñez
updated: 2026-08-16
---
# DEVPL-GSDLC-02-B — Candidate closure report

## Result
`PASS-CANDIDATE/PRE-WINDOWS`. Owner closure remains pending Windows execution/evidence.

## Implemented
- typed `AuthenticatedPrincipal`, `LocalIdentity`, `CredentialRecord`, `SessionRecord`, `SessionContext`, `SessionRevocation`;
- runtime-only versioned SQLite `LocalAuthStore` outside Git/evidence;
- stdlib scrypt-v1 credential KDF with random salt/versioned parameters;
- first owner bootstrap exactly once;
- login, session create/inspect/rotate, idle timeout, absolute timeout, revoke and logout;
- sanitized auth audit trail;
- seven localhost-only auth API routes;
- HttpOnly/SameSite session cookie, CSRF digest/header and local Origin controls;
- legacy local token explicitly blocked from human-only session routes and approval decision endpoints;
- additive OpenAPI/API registry contract evolution preserving historical metadata.

## Validation

Controlled pre-Windows validation is complete:

- three non-overlapping security/API/contract groups: `72 + 61 + 17 = 150 PASS`, zero failures/errors/skips;
- Project State: `PASS`;
- Docs Governance: `PASS`;
- TCR v1: `PASS`;
- TCR v2: `PASS`;
- Test Impact: `REVIEW_REQUIRED`, 58 changed paths, 156 matched contracts, 254 recommended tests, 19 unmatched paths, residual risk `high`, full regression recommended;
- hard-trigger review: `false`;
- Historical Regression Guard: `PASS`, cadence waiver valid, 5/5 guard components PASS, 0 warnings/blocking findings;
- full regression: **not executed** in this intermediate micro-sprint and deferred to `DEVPL-GSDLC-02-E`.

The Test Impact full-regression recommendation is not suppressed: it is explicitly recorded and adjudicated under the owner-approved A→D cumulative-selective policy.

## Limitations / future evolution
This is an **initial local authentication implementation**, not enterprise IAM. Argon2id remains a future hardening option. 02-C must implement exhaustive server-side RBAC/workspace scope and role invalidation. 02-D must make approval actor binding fully session-derived/non-spoofable. 02-E must implement high-quality login/first-run/session UX and browser security acceptance.

## Recovery v1.0.1 — Windows portability and current-active operator flow

The first Windows validation attempt blocked before group 2 for two independent causes:

1. the symlink-negative test required Windows symlink privilege and failed with WinError 1314 before exercising LocalAuthStore;
2. POST-H-028-D OperatorFlowSmoke still denied an approval with the legacy local token after 02-B correctly made approval decisions human-session-required.

The successor correction:
- separates path-escape from symlink traversal tests and skips only the real symlink case when Windows explicitly reports privilege error 1314;
- evolves OperatorFlowSmoke as `current-active`: its temporary sandbox bootstraps a local owner session, uses CSRF for mutation, and performs the approval decision as a human session;
- does **not** restore legacy-token approval authority;
- keeps UI/browser work deferred to 02-E and full regression deferred to 02-E.

Final delta: 59 paths (36 CREATE, 23 MODIFY, 0 DELETE).

## Recovery v1.0.3 — cumulative historical-contract reconciliation

Independent A+B verification of the published repo355 candidate found one inherited 02-A assertion that incorrectly froze
`.devpilot/interfaces/api_route_contract_registry.json` to its repo353 Git-blob SHA. That registry is explicitly
`current-active` in the 02-B historical sweep and legitimately evolves from 89 to 96 routes when the seven local-auth
routes are introduced.

The recovery does not weaken or rewrite the 02-A historical facts. It:
- keeps the repo353 Git-blob freeze for `identity_registry.json` and `sensitive_action_catalog.json`;
- removes only the obsolete freeze of the current-active API route registry;
- adds a 02-B successor assertion for all seven auth routes, the 96-route total and no remote/external routes;
- changes no runtime product behavior;
- keeps the backlog-wide full regression deferred to 02-E.

02-B remains `PASS-CANDIDATE` pending Windows execution of this recovery and owner adjudication.

### Controlled recovery validation

Before distribution, the reconciliation candidate was validated independently with non-overlapping selective sets:

- 02-A + 02-B auth/contracts focal: `26 PASS`;
- 02-B API/security/contract-drift: `69 PASS`;
- secret guard/security readiness: `6 PASS`;
- aggregate non-overlapping controlled recovery set: `101 PASS / 0 FAIL / 0 ERROR / 0 SKIP`;
- Project State, Docs Governance, TCR v1 and TCR v2: `PASS`;
- Test Impact: `REVIEW_REQUIRED`, 60 changed paths, residual risk `high`;
- Historical Regression Guard: `PASS`, waiver valid, 5/5 components, 0 warnings/blockers.

The complete Windows cumulative groups remain mandatory in the recovery operator before publish.
