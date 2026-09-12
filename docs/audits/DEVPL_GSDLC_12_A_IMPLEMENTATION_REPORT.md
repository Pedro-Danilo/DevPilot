---
doc_id: "DEVPL-GSDLC-12-A-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-12-A — Persistent resumability, crash/restart recovery and locks"
status: "implemented-local-qualified/windows-validation-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-12"
approval: "pending_windows_validation"
---

# 1. Source authority and activation

Implementation is cumulative from repo425, commit `b341370633e66355add6bb2611879b32f277ad0f`, SHA-256 `d4a9cf4b3b8d544b71ee9b568e7ba3388cf39e74ce8d213d3b0e9f9d2946695d`. Activation/rebind is absorbed into 12-A. GSDLC-11 historical Full/browser/composite evidence is preserved. GSDLC-12 starts budget `0/1`; Full Regression in 12-A is `0`.

# 2. Implemented capabilities

- `ResumeService`: versioned metadata-only checkpoint, source/session/actor/approval revalidation, recovery states `SAFE_TO_RESUME`, `REVALIDATION_REQUIRED`, `ABORTED_REQUIRES_REPLAN`, `COMPLETED`.
- `WorkspaceLockService`: exclusive per workspace/action locks, exact actor/session ownership, heartbeat, stale detection, explicit authorized stale recovery and mandatory revalidation for sensitive work.
- `RecoveryApplicationService` + project-scoped `/api/v1/recovery*` typed routes with PolicyEngine/RBAC bindings.
- `RecoveryView`: server-authoritative recovered context, pending work, locks, next action and Project Status coherence. No `sessionStorage`/`localStorage` authority.
- Project Status successor reconciliation: `Lifecycle RELEASED` remains display-authoritative when remaining gaps are non-authoritative post-release domains; real release/git/security/revalidation/source/runtime blockers still produce BLOCKED.
- Current-active activation surfaces are rebound to GSDLC-12-A while repo425 remains the canonical execution baseline until Windows PASS creates a successor.

# 3. Safety

No automatic mutation replay, arbitrary shell, remote operation, runtime DB snapshot, destructive Git, push/publish/deploy or external API is introduced. Recovery persistence writes only bounded metadata under platform `outputs/`; managed workspace source remains unchanged.

# 4. Validation

Local qualification: GSDLC-12-A focal recovery 11/11 PASS; predecessor historical-contract reconciliation 13/13 PASS; selected auth/project-entry cumulative checks 24/24 PASS; UI recovery smoke 10/10 PASS; Project State/TCR v1/TCR v2/Test Impact Rules/Test Impact/HCA/Contract Reconciliation PASS. Test Impact = 50/216/336/0. The global docs-governance CLI exceeded this sandbox time budget and is therefore not claimed PASS locally; Windows validation uses bounded frontmatter/current-authority checks instead of repeating an expensive unrelated global scan. Real browser restart acceptance remains mandatory on Windows. Full Regression = 0.

# 5. Preliminary limitations

This is the first local industrial recovery version. Locks are local-filesystem scoped, not distributed. Branch/external edit conflict UX belongs to GSDLC-12-B. Accessibility/mode parity and red-team/performance hardening remain in 12-C/12-D. Full browser matrix and the only GSDLC-12 Full belong to 12-E.
