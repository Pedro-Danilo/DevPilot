---
doc_id: "DEVPL-UX-P0-A-FRONTEND-METADATA-RECONCILIATION"
title: "DEVPL-UX-P0-A — Frontend metadata reconciliation"
status: "implemented/local-qualified/windows-validation-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "implementation_evidence_pending_windows"
---

# Frontend metadata reconciliation

`ui/web/package.json` is advanced to `0.38.0-ux-p0-a` and declares `currentSprint=DEVPL-UX-P0-A`. `package-lock.json` root metadata is synchronized. No dependency is added or removed.

UX-P0-A records `uxP0RoutePathsChanged=false`, `uxP0ServerAuthorityChanged=false`, and `uxP0FullRegressionRuns=0`.

The CSS foundation adds semantic tokens while preserving the initial repo430 visual values. A dependency-free `test:ux-p0-a` smoke verifies token presence/adoption, Project State rebind and key route preservation.

## Risks and limitations

- Historical metadata remains preserved in historical documents/snapshots; this report only advances current-active frontend identity.
- UX-P0-A does not claim final production visual quality.

## PASS/BLOCK

**PASS:** package/package-lock current identity is synchronized, no dependency set changes, route paths remain unchanged and Full=0.

**BLOCK:** dependency drift, stale current sprint metadata, route/policy mutation or package/package-lock version mismatch.

## Verification commands

```text
cd ui/web && npm run test:ux-p0-a
python -m pytest tests/test_devpl_ux_p0_a_foundation_contracts.py -q
```

