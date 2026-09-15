---
doc_id: "DEVPL-UX-P0-A-DESIGN-SYSTEM-FOUNDATION"
title: "DevPilot UX-P0-A — Design system foundation contract"
status: "current"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "derived_from_approved_DEVPL-UX-P0-A"
---

# Design system foundation contract

UX-P0-A establishes semantic primitives, not a visual redesign. Values map current repo430 visual semantics so adoption is low-risk.

Domains: typography, canvas/surface/text, borders, actions/focus, operational status states, spacing, radii, elevation and minimum interaction target.

No dependency or framework is introduced. Existing `styles.css` remains the compatibility layer and consumes tokens for shared primitives. Route-specific hardcoded styling is intentionally migrated later when the related surface is productized.

**No ADR is created in UX-P0-A** because no architectural boundary, runtime framework, route authority or shell extraction changes in this micro-sprint.

## Risks and limitations

- Token introduction is intentionally semantics-preserving; visual hierarchy/product polish is deferred to UX-P0-B/C/D.
- Remaining hard-coded route-specific styles are tracked UX-S3 debt, not a reason for mass migration in A.

## PASS/BLOCK

**PASS:** semantic domains exist, current visual values remain equivalent, accessibility targets remain valid and no dependency/framework is added.

**BLOCK:** tokenization changes route authority, weakens a11y minimums, hides blockers or introduces an unapproved runtime dependency.

## Verification commands

```text
cd ui/web && npm run test:ux-p0-a
cd ui/web && npm run test:accessibility
cd ui/web && npm run test:state-matrix
```

