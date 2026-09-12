---
doc_id: "ADR-DEVPL-GSDLC-12-A-RECOVERY-AUTHORITY"
title: "Durable recovery metadata and workspace lock authority"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-12"
approval: "approved_by_owner/GSDLC-12-A-scope"
---

# Context
GSDLC-12-A requires restart/crash resumability without making browser storage or runtime authentication databases authoritative and without replaying incomplete mutations.

# Decision
DevPilot stores only bounded recovery metadata under `outputs/workspaces/<workspace_id>/recovery/`: a versioned checkpoint and per-action lock records. Source/Git identity and workspace scope are re-observed server-side on every recovery. Browser storage remains UX-only. `auth.db*`, `devpilot.db*`, secrets and managed source contents are not copied into the recovery store.

Sensitive or incomplete work is never auto-executed. Source/session/actor/approval drift yields `REVALIDATION_REQUIRED` or `ABORTED_REQUIRES_REPLAN`. Locks use exclusive creation, exact actor/session ownership, bounded TTL and explicit stale recovery by authorized human confirmation. Stale recovery never grants execution authority.

# Consequences
- Restart can recover safe references and current-step context without replaying side effects.
- Crash recovery is explainable and fail-closed.
- Runtime DB loss does not silently convert browser state into authority.
- GSDLC-12-B may later reconcile branch/filesystem drift against the same authoritative Git identity model.

# Non-goals
No distributed lock service, cloud coordination, remote execution, autonomous mutation replay or cross-machine failover is introduced in this first local industrial version.
