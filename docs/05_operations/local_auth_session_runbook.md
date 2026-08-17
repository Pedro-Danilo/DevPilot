---
doc_id: DEVPL-GSDLC-02-B-AUTH-RUNBOOK
title: Local authentication and session operations runbook
status: implemented-initial
version: 1.0.0
owner: Ordóñez
updated: 2026-08-16
---
# Local auth/session runbook

## Runtime data
`.devpilot/auth/auth.db` is runtime-only. Never add it to Git, source ZIP, evidence ZIP, screenshots or support bundles. Back up/restore procedures for credentials are not yet production-grade and remain future hardening work.

## First run
Bootstrap is available only when no active owner exists. The first owner receives actor id `local-owner`, role `owner`, scope `devpilot-local`. A second bootstrap is blocked transactionally.

## Session operations
Login verifies scrypt credentials and creates an opaque session. Protected human-session endpoints accept the session cookie, not a request actor. Rotation revokes old first. Logout/revoke invalidate immediately. Idle and absolute expiry revoke on resolve.

## Browser transport
Use loopback API/UI only. Public browser login/bootstrap POSTs reject non-local Origin. Authenticated mutating requests require local Origin (when provided) plus `X-DevPilot-CSRF`. The login UI itself is intentionally deferred to GSDLC-02-E.

## Recovery
Restart recovery reopens the same versioned SQLite store and validates existing opaque session digests. Corrupt/incompatible store fails closed. Administrative owner recovery is not implemented in 02-B; do not delete/replace the database as an automatic recovery action.
