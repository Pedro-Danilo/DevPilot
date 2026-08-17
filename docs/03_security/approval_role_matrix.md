---
doc_id: "DEVPL-GSDLC-02-D-APPROVAL-ROLE-MATRIX"
title: "Approval role and separation-of-duties matrix"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-17"
approval: "approved_by_owner"
---

# Approval role matrix

The machine-readable authority is `.devpilot/approval/approval_authority_matrix.json`.

- low: broad authenticated local roles;
- medium: review/management roles, excluding developer/operator;
- high: domain-bounded roles; workspace/filesystem/Git remain owner-only;
- critical: explicit domain authority only; no wildcard and no critical self-approval.

`reviewer` remains an alias only for `qa-reviewer`; it is not a security-reviewer. The legacy `maintainer` role is not revived as runtime authority.

Role/session revocation and workspace mismatch fail closed. The legacy local API token is never human approval authority.
