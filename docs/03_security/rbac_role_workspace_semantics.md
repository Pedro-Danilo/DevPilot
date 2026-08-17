# RBAC role/workspace semantics — GSDLC-02-C

- Roles come only from `AuthenticatedPrincipal` resolved from the server-side session.
- `reviewer` is an explicit compatibility alias for `qa-reviewer`; it never implies `security-reviewer`.
- The historical catalog-only `maintainer` is not a valid runtime principal. Its three blocked actions receive owner-only successor authorization metadata but remain blocked/non-executable in the original sensitive-action catalog.
- Workspace-bound operations require a scope carried by the principal. Cross-workspace attempts are DENY.
- Role/scope changes revoke active sessions atomically; stale session authority fails closed.
- There is no role self-service endpoint in 02-C.
