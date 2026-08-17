---
doc_id: "DEVPL-GSDLC-02-D-AUTHENTICATED-APPROVAL-BINDING"
title: "Authenticated Approval Binding"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-17"
approval: "approved_by_owner"
---

# Authenticated Approval Binding

GSDLC-02-D converts approval authority from caller-supplied actor strings to the authenticated human session.

`session -> AuthenticatedPrincipal -> server RBAC -> approval authority matrix -> AuthenticatedApprovalBinding`

The binding persists no raw session token, cookie or CSRF secret. A safe session binding id is derived from actor, session creation timestamp and rotation counter. Current executable sensitive actions require this D binding and revalidate the decision session plus current identity roles/scopes before execution.

High-risk self approval is denied by default. A single narrow owner exception exists for high-risk local workspace/filesystem/Git actions because the current local-first bootstrap creates one owner. Critical self-approval remains denied.

Actor fields retained in old request DTOs are deprecated compatibility hints and cannot override the authenticated principal. Actor-based CLI approval decisions are disabled once the D authority matrix exists.

This is an initial local-first implementation, not enterprise IAM or multi-tenant approval governance.
