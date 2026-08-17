---
doc_id: DEVPL-GSDLC-02-B-LOCAL-IDENTITY-SESSION-CONTRACT
title: Local identity, credential and session runtime contract
status: implemented-initial
version: 1.0.0
owner: Ordóñez
updated: 2026-08-16
---
# Local identity/session contract

GSDLC-02-B introduces the first runtime implementation of `local.operator_auth`. It is **preliminary/initial**, local-only and intentionally narrower than production enterprise IAM.

## Boundaries

- `AuthenticatedPrincipal` is created only from a verified human session.
- `legacy-local-token` remains compatibility-only and is never a human principal.
- Request-supplied `actor_id` is not authentication authority.
- Approval actor binding remains GSDLC-02-D; 02-B only blocks legacy-token-only approval decisions.
- RBAC enforcement by endpoint/action/workspace remains GSDLC-02-C.

## Runtime store

SQLite: `.devpilot/auth/auth.db`, ignored from Git/source/evidence. Schema version 1. Store writes are transactional; corruption/incompatible schema fails closed. Raw password, raw session token and raw CSRF token are never persisted.

## Session model

Opaque random session token -> SHA-256 lookup digest at rest. CSRF token -> SHA-256 digest at rest. Default idle timeout 30 min; absolute timeout 8 h. Rotation revokes old session in the same transaction before issuing the replacement. Logout/revoke invalidate immediately.

## Transport

Session cookie: HttpOnly, SameSite=Strict, Path=/; Secure when HTTPS. Localhost HTTP development cannot use Secure cookies, so loopback-only bind + strict CORS/origin + CSRF controls are mandatory. CSRF uses a non-HttpOnly double-submit delivery cookie plus server-side digest validation and `X-DevPilot-CSRF` header. No browser storage of auth secrets is introduced in 02-B.
