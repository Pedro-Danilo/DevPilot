---
doc_id: "DEVPL-GSDLC-03-C-CLOSURE-REPORT"
title: "DEVPL-GSDLC-03-C — Dry-run Create/Open/Import closure report"
status: "pass-candidate/pre-windows"
version: "1.0.2"
owner: "Ordóñez"
updated: "2026-08-18"
approval: "pending_owner_adjudication"
---

# DEVPL-GSDLC-03-C — Closure report

03-C implements review-only CREATE_NEW, OPEN_EXISTING and IMPORT_GIT dry-runs through ApplicationService/API/UI. Each dry-run carries stable plan/preimage hashes, explicit side effects and a typed approval preview. Revalidation blocks stale preimages.

No execute route exists. Product writes, network runtime, approval mutation, external APIs and pilot workspace access remain disabled. Remote Git is plan-only. Full regression is deferred to 03-E.


## Browser boundary corrective v1.0.2

Windows browser acceptance exposed two coupled defects before closure:

1. The API process had no `DEVPILOT_ALLOWED_WORKSPACE_ROOTS` binding, so the correct E2E fixture target was blocked by PathGuard.
2. An empty `target_root` bypassed runtime target validation and later resolved to the DevPilot repository working directory. That apparent PASS is invalid evidence and is now blocked by `PROJECT_INTAKE_TARGET_REQUIRED`.

The UI now requires a non-empty target, 403 diagnostics preserve the backend finding instead of mislabeling every 403 as an invalid local token, and browser acceptance must bind the API process to the exact fixture root. No project write/network action is enabled.
